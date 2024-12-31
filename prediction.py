import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from typing import List, Tuple, Dict
import datetime

class MatchPredictor:
    def __init__(self):
        """Initialize the match predictor with default parameters"""
        self.rf = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=1)
        self.matches = None
        self.matches_rolling = None
        self.predictors = ['venue_code', 'opp_code', 'hour', 'day_code']
        self.rolling_stats = ['gf', 'ga', 'sh', 'sot', 'dist', 'fk', 'pk', 'pkatt']
        
    def load_data(self, filepath: str) -> None:
        """Load and prepare the match data"""
        self.matches = pd.read_csv(filepath, index_col=0)
        self._encode_categorical_columns()
        self._create_rolling_averages()
        
    def _encode_categorical_columns(self) -> None:
        """Encode categorical variables for model input"""
        mapping = {'Home': 1, 'Away': 0}
        self.matches['venue_code'] = self.matches['venue'].map(mapping)
        
        # Create opponent codes
        opponents = sorted(self.matches['opponent'].unique())
        opp_mapping = {opponent: idx for idx, opponent in enumerate(opponents)}
        self.matches['opp_code'] = self.matches['opponent'].map(opp_mapping)
        
        # Extract hour from time
        self.matches['hour'] = pd.to_datetime(self.matches['time'], format='%H:%M').dt.hour
        
        # Encode day of week
        day_mapping = {day: idx for idx, day in enumerate(self.matches['day'].unique())}
        self.matches['day_code'] = self.matches['day'].map(day_mapping)

    def _create_rolling_averages(self, window: int = 3) -> None:
        """Create rolling averages for specified statistics"""
        self.matches_rolling = self.matches.copy()
        
        # Sort by date within each team group
        self.matches_rolling = self.matches_rolling.sort_values(['team', 'date'])
        
        # Calculate rolling averages for each statistic
        for stat in self.rolling_stats:
            # Calculate rolling average within each team group
            rolling_stat = (self.matches_rolling
                           .groupby('team')[stat]
                           .transform(lambda x: x.rolling(window, min_periods=1).mean()))
            
            # Assign the rolling average back to the dataframe
            self.matches_rolling[f'{stat}_rolling'] = rolling_stat

    def prepare_features(self) -> None:
        """Prepare features for model training"""
        # Create target variable (1 for win, 0 for loss/draw)
        self.matches_rolling['target'] = (self.matches_rolling['result'] == 'W').astype(int)
        
        # Add rolling stats to predictors
        self.rolling_predictors = [f'{stat}_rolling' for stat in self.rolling_stats]
        self.all_predictors = self.predictors + self.rolling_predictors

    def make_predictions(self, method='date', cutoff_date='2022-01-01', train_ratio=0.8) -> Tuple[pd.DataFrame, float]:
        """
        Make predictions using the random forest model
        
        Args:
            method: 'date' for fixed cutoff date or 'ratio' for ratio-based split
            cutoff_date: Date to split training/test data if method='date'
            train_ratio: Ratio of data to use for training if method='ratio'
            
        Returns:
            Tuple containing predictions DataFrame and model error
        """
        # Sort data by date
        self.matches_rolling = self.matches_rolling.sort_values('date')
        
        # Split data based on chosen method
        if method == 'date':
            train = self.matches_rolling[self.matches_rolling['date'] < cutoff_date]
            test = self.matches_rolling[self.matches_rolling['date'] >= cutoff_date]
        else:  # ratio-based split
            split_idx = int(len(self.matches_rolling) * train_ratio)
            train = self.matches_rolling.iloc[:split_idx]
            test = self.matches_rolling.iloc[split_idx:]
        
        print(f"\nTraining Data Period: {train['date'].min()} to {train['date'].max()}")
        print(f"Testing Data Period: {test['date'].min()} to {test['date'].max()}")
        print(f"Total matches: {len(self.matches_rolling)}")
        print(f"Training matches: {len(train)}")
        print(f"Testing matches: {len(test)}")
        
        # Fit model and make predictions
        self.rf.fit(train[self.all_predictors], train['target'])
        preds = self.rf.predict(test[self.all_predictors])
        
        # Create results DataFrame
        combined = pd.DataFrame({
            'actual': test['target'],
            'predicted': preds,
            'date': test['date'],
            'team': test['team'],
            'opponent': test['opponent'],
            'result': test['result']
        })
        
        # Calculate error using precision score
        error = precision_score(test['target'], preds)
        
        # Print detailed performance metrics
        print(f"\nModel Performance:")
        print(f"Precision Score: {error:.3f}")
        print(f"Correct Predictions: {(combined['actual'] == combined['predicted']).sum()}")
        print(f"Total Predictions: {len(combined)}")
        print(f"Accuracy: {(combined['actual'] == combined['predicted']).mean():.3f}")
        
        return combined, error

    def analyze_predictions(self, predictions: pd.DataFrame) -> Dict:
        """
        Analyze prediction results
        
        Returns:
            Dictionary containing various analysis metrics
        """
        correct_predictions = (predictions['actual'] == predictions['predicted']).sum()
        total_predictions = len(predictions)
        accuracy = correct_predictions / total_predictions
        
        analysis = {
            'accuracy': accuracy,
            'total_matches': total_predictions,
            'correct_predictions': correct_predictions,
            'win_rate': predictions['actual'].mean(),
            'predicted_win_rate': predictions['predicted'].mean()
        }
        
        return analysis

    def predict_upcoming_match(self) -> float:
        """
        Interactive function to predict an upcoming match based on user input
        """
        print("\n=== Match Prediction System ===")
        
        # Get user input
        team = input("Enter team name (e.g., Manchester City): ").strip()
        opponent = input("Enter opponent name: ").strip()
        venue = input("Is it a home game? (yes/no): ").strip().lower()
        time = input("Enter kickoff time (HH:MM, e.g., 15:30): ").strip()
        day = input("Enter day of week (Mon/Tue/Wed/Thu/Fri/Sat/Sun): ").strip()

        # Validate team names
        if team not in self.matches['team'].unique():
            print(f"\nError: Team '{team}' not found in database.")
            print("Available teams:", ', '.join(sorted(self.matches['team'].unique())))
            return None
            
        if opponent not in self.matches['opponent'].unique():
            print(f"\nError: Opponent '{opponent}' not found in database.")
            print("Available opponents:", ', '.join(sorted(self.matches['opponent'].unique())))
            return None

        # Get recent stats for the team
        recent_matches = self.matches_rolling[
            (self.matches_rolling['team'] == team)
        ].sort_values('date', ascending=False).head(3)

        if len(recent_matches) < 3:
            print(f"\nWarning: Only {len(recent_matches)} recent matches found for {team}")

        # Prepare match data
        match_data = {
            'team': team,
            'opponent': opponent,
            'venue': 'Home' if venue.startswith('y') else 'Away',
            'time': time,
            'day': day,
            'venue_code': 1 if venue.startswith('y') else 0,
            'opp_code': self.matches['opp_code'][self.matches['opponent'] == opponent].iloc[0],
            'hour': pd.to_datetime(time, format='%H:%M').hour,
            'day_code': self.matches['day_code'][self.matches['day'] == day].iloc[0]
        }

        # Add rolling averages
        for stat in self.rolling_stats:
            match_data[f'{stat}_rolling'] = recent_matches[stat].mean()

        # Prepare features for prediction
        pred_df = pd.DataFrame([match_data])
        
        # Make prediction
        win_prob = self.rf.predict_proba(pred_df[self.all_predictors])[0][1]
        
        # Print detailed results
        print("\n=== Prediction Results ===")
        print(f"Match: {team} vs {opponent}")
        print(f"Venue: {'Home' if venue.startswith('y') else 'Away'}")
        print(f"Time: {time} on {day}")
        print(f"\nWin Probability: {win_prob:.1%}")
        
        # Provide interpretation
        print("\nInterpretation:")
        if win_prob >= 0.6:
            print(f"Strong chance of {team} winning")
        elif win_prob >= 0.4:
            print(f"Match could go either way")
        else:
            print(f"Lower chance of {team} winning")
            
        return win_prob

def main():
    # Initialize predictor
    predictor = MatchPredictor()
    
    # Load and prepare data
    print("Loading and preparing data...")
    predictor.load_data("matches.csv")
    predictor.prepare_features()
    
    # Train the model
    print("Training model...")
    predictor.make_predictions()
    
    # Interactive prediction loop
    while True:
        predictor.predict_upcoming_match()
        
        # Ask if user wants to predict another match
        again = input("\nPredict another match? (yes/no): ").strip().lower()
        if not again.startswith('y'):
            break

if __name__ == "__main__":
    main()
