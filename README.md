# EPL Match Predictor

Hi, this is a machine learning-based web application that predicts English Premier League match outcomes using historical data from 2020-2022 seasons.

## How It Works

### Data Processing
- Uses historical EPL match data CSV filefrom 2020-2022 seasons
- Processes categorical variables (teams, venues) into numerical format
- Calculates rolling averages for team performance metrics:
  - Goals scored/conceded
  - Shots on target
  - Possession percentages
  - Other match statistics

### Model Training
The system tests two different training approaches and automatically selects the better performing one:
1. Date-based split:
   - Training data: Matches before 2022-01-01
   - Testing data: Matches after 2022-01-01

2. Ratio-based split:
   - 80% of data for training
   - 20% of data for testing

### Prediction Process
Users can input:
- Home team
- Away team
- Match venue (Home/Away)
- Kickoff time
- Day of the week

The model returns:
- Win probability percentage
- Confidence category (High/Medium/Low)
- Interpretive prediction message

### Web Interface
- Interactive form for match data input
- Visual representation of prediction results
- Responsive design with dynamic background
- Real-time form validation

## Lanugages/Technologies Used
- Python (Flask, Pandas, Scikit-learn)
- HTML/CSS/JavaScript
- Random Forest Classifier
- Bootstrap for UI components

## Setup and Usage
1. Install requirements: `pip install -r requirements.txt`
2. Run the application: `python app.py`
3. Access via browser at `http://localhost:5000`
4. Enter the match data and click "Predict" to see the results.

## Future Improvements
- Use more recent data
- Use more datasets to train the model and improve accuracy


Project inspired by Dataquest Tutorial
"# EPL-Match-Result-Predictor" 
