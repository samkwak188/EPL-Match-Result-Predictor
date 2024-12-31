from flask import Flask, render_template, request, jsonify
from prediction import MatchPredictor
import pandas as pd

app = Flask(__name__)
predictor = MatchPredictor()

# Initialize and train the model when starting the app
print("Loading and preparing data...")
predictor.load_data("matches.csv")
predictor.prepare_features()

# Try both methods and use the better one
print("\nTesting date-based split...")
predictions_date, error_date = predictor.make_predictions(method='date', cutoff_date='2022-01-01')

print("\nTesting ratio-based split...")
predictions_ratio, error_ratio = predictor.make_predictions(method='ratio', train_ratio=0.8)

# Use the better performing method
if error_date > error_ratio:
    print("\nUsing date-based split (better performance)")
    predictions, error = predictions_date, error_date
else:
    print("\nUsing ratio-based split (better performance)")
    predictions, error = predictions_ratio, error_ratio

@app.route('/')
def home():
    # Get unique teams directly from the CSV file
    teams = sorted(predictor.matches['team'].unique())  # For team selection
    opponents = sorted(predictor.matches['opponent'].unique())  # For opponent selection
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Print available teams for debugging
    print("\nAvailable teams in database:")
    print(teams)
    
    return render_template('index.html', teams=teams, opponents=opponents, days=days)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Validate team and opponent exist in the database
        if data['team'] not in predictor.matches['team'].unique():
            return jsonify({
                'success': False,
                'error': f"Team '{data['team']}' not found in database"
            })
            
        if data['opponent'] not in predictor.matches['opponent'].unique():
            return jsonify({
                'success': False,
                'error': f"Opponent '{data['opponent']}' not found in database"
            })

        # Get recent stats for the team
        recent_matches = predictor.matches_rolling[
            (predictor.matches_rolling['team'] == data['team'])
        ].sort_values('date', ascending=False).head(3)

        if len(recent_matches) == 0:
            return jsonify({
                'success': False,
                'error': f"No recent matches found for {data['team']}"
            })

        # Safely get opponent code
        opp_codes = predictor.matches[predictor.matches['opponent'] == data['opponent']]['opp_code']
        if len(opp_codes) == 0:
            return jsonify({
                'success': False,
                'error': f"No data found for opponent {data['opponent']}"
            })
        opp_code = opp_codes.iloc[0]

        # Safely get day code
        day_codes = predictor.matches[predictor.matches['day'] == data['day']]['day_code']
        if len(day_codes) == 0:
            return jsonify({
                'success': False,
                'error': f"Invalid day of week: {data['day']}"
            })
        day_code = day_codes.iloc[0]

        # Prepare match data
        try:
            match_data = {
                'team': data['team'],
                'opponent': data['opponent'],
                'venue': 'Home' if data['venue'] == 'home' else 'Away',
                'time': data['time'],
                'day': data['day'],
                'venue_code': 1 if data['venue'] == 'home' else 0,
                'opp_code': opp_code,
                'hour': pd.to_datetime(data['time'], format='%H:%M').hour,
                'day_code': day_code
            }

            # Add rolling averages with error handling
            for stat in predictor.rolling_stats:
                match_data[f'{stat}_rolling'] = recent_matches[stat].mean()
                if pd.isna(match_data[f'{stat}_rolling']):
                    match_data[f'{stat}_rolling'] = 0  # Use 0 as fallback for missing stats

            # Prepare features for prediction
            pred_df = pd.DataFrame([match_data])
            
            # Ensure all required features are present
            missing_features = [f for f in predictor.all_predictors if f not in pred_df.columns]
            if missing_features:
                return jsonify({
                    'success': False,
                    'error': f"Missing required features: {', '.join(missing_features)}"
                })
            
            # Make prediction
            win_prob = float(predictor.rf.predict_proba(pred_df[predictor.all_predictors])[0][1])
            
            # Determine prediction category
            if win_prob >= 0.6:
                category = "high"
                message = f"Strong chance of {data['team']} winning"
            elif win_prob >= 0.4:
                category = "medium"
                message = "Match could go either way"
            else:
                category = "low"
                message = f"Lower chance of {data['team']} winning"

            return jsonify({
                'success': True,
                'probability': round(win_prob * 100, 1),
                'category': category,
                'message': message
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error processing match data: {str(e)}"
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(debug=True) 