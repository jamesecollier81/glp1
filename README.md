# GLP-1 Injection Tracker

A Streamlit web application for tracking GLP-1 injections, weight, and side effects.

## Features

- **Injection Tracking**: Log date, time, dosage, weight, and notes
- **Side Effects Tracking**: Record side effects with dates and descriptions
- **Analytics Dashboard**:
  - Weight trend charts
  - Dosage tracking over time
  - Side effects timeline correlation
  - Summary statistics

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment to Streamlit Cloud

1. Push this code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub repository
5. Set the main file path to `app.py`
6. Click "Deploy"

## Data Storage

The app stores data in CSV files:
- `injections.csv`: Injection records
- `side_effects.csv`: Side effect records

These files are created automatically when you first use the app.

## Usage Tips

- Log injections consistently for better tracking
- Record weight at the same time of day for accuracy
- Note any side effects, even minor ones
- Use the Analytics page to monitor trends and correlations