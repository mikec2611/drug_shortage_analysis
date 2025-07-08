# 🩺 Drug Shortage Prediction Dashboard

An interactive web dashboard for predicting drug shortages using machine learning and D3.js visualizations.

## 🌟 Features

### **Interactive Visualizations**
- **Risk Distribution** - Pie chart showing High/Medium/Low risk drugs
- **Model Performance** - Bar chart comparing ML model accuracy
- **Feature Importance** - Horizontal bar chart of predictive features
- **Shortage Timeline** - Time series of historical shortages
- **Company Risk Analysis** - Risk scores by pharmaceutical company
- **Drug Categories** - Therapeutic categories most at risk

### **Real-time Analytics**
- **Live Predictions** - ML-powered shortage probability scores
- **Interactive Filters** - Filter by risk level, company, or drug name
- **Search Functionality** - Search specific drugs for risk assessment
- **Responsive Design** - Works on desktop and mobile devices

### **Dashboard Components**
- **Summary Cards** - Key metrics at a glance
- **Predictions Table** - Top at-risk drugs with action recommendations
- **Dynamic Updates** - Real-time data filtering and updates
- **Hover Tooltips** - Interactive data exploration

## 🚀 Quick Start

### **Prerequisites**
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure database is set up with .env file
DB_HOST=your_host
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_PORT=5432
```

### **Run the Dashboard**
```bash
# Start the Flask server
python app.py

# Access the dashboard
# Open browser to: http://localhost:5000
```

### **Alternative: Run with ML Analysis**
```bash
# Run ML pipeline first (optional)
python run_ml_analysis.py

# Then start dashboard
python app.py
```

## 📊 Dashboard Sections

### **1. Summary Cards**
- **Total Shortage Records** - Historical shortage count
- **Total Enforcement Records** - FDA enforcement actions
- **High Risk Drugs** - Current high-risk drug count
- **Model Accuracy** - Best performing ML model score

### **2. Interactive Controls**
- **Risk Level Filter** - Filter predictions by High/Medium/Low
- **Company Filter** - Search and filter by company name
- **Drug Search** - Find specific drug risk assessments

### **3. Visualizations**
- **Risk Distribution** - Pie chart with color-coded risk levels
- **Model Performance** - AUC scores for all ML models
- **Feature Importance** - Top predictive features from Random Forest
- **Shortage Timeline** - Monthly shortage trends over time
- **Company Risk** - Risk scores combining shortages + enforcements
- **Drug Categories** - Therapeutic categories with most shortages

### **4. Predictions Table**
- **Drug Name** - Generic drug name
- **Company** - Manufacturing company
- **Risk Level** - Color-coded risk assessment
- **Probability** - Shortage probability percentage
- **Action** - Recommended monitoring level

## 🔧 API Endpoints

The dashboard provides RESTful API endpoints:

- `GET /api/summary` - Database summary statistics
- `GET /api/predictions` - ML predictions with filtering
- `GET /api/model_performance` - Model performance metrics
- `GET /api/feature_importance` - Feature importance data
- `GET /api/shortage_timeline` - Historical shortage timeline
- `GET /api/enforcement_timeline` - Enforcement action timeline
- `GET /api/company_risk` - Company risk analysis
- `GET /api/drug_categories` - Drug category analysis
- `GET /api/risk_distribution` - Risk level distribution
- `GET /api/search_drug?drug_name=<name>` - Search specific drug
- `GET /api/health` - Health check endpoint

## 🎨 Visualization Details

### **Chart Types**
- **Bar Charts** - Model performance, feature importance, company risk
- **Pie Chart** - Risk distribution with legend
- **Line Chart** - Time series for shortage trends
- **Horizontal Bars** - Feature importance and company rankings
- **Interactive Table** - Sortable predictions with risk badges

### **Color Scheme**
- **High Risk** - Red (#ff6b6b)
- **Medium Risk** - Orange (#ffa726)
- **Low Risk** - Green (#66bb6a)
- **Primary** - Blue (#4a90e2)
- **Secondary** - Purple (#7b68ee)
- **Accent** - Teal (#20b2aa)

### **Interactions**
- **Hover Effects** - Tooltips with detailed information
- **Click Actions** - Filtering and drill-down capabilities
- **Responsive Design** - Adapts to different screen sizes
- **Smooth Animations** - Transitions between states

## 🛠️ Technical Stack

### **Backend**
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Database
- **Pandas** - Data manipulation
- **Scikit-learn** - Machine learning
- **XGBoost** - Gradient boosting

### **Frontend**
- **D3.js** - Interactive visualizations
- **HTML5/CSS3** - Modern web standards
- **JavaScript ES6** - Async/await, modules
- **Responsive Grid** - CSS Grid and Flexbox

### **Data Flow**
1. **Data Extraction** - PostgreSQL → Pandas DataFrames
2. **ML Pipeline** - Feature engineering → Model training
3. **API Layer** - Flask routes → JSON responses
4. **Frontend** - D3.js → Interactive charts
5. **User Interface** - Real-time updates → User interactions

## 🚀 Deployment

### **Local Development**
```bash
# Development mode
python app.py
# Flask runs on http://localhost:5000
```

### **Production**
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📈 Performance

- **Real-time Updates** - Sub-second chart updates
- **Efficient Queries** - Optimized database queries
- **Caching** - In-memory caching for frequently accessed data
- **Responsive Design** - Smooth performance across devices

## 🔒 Security

- **Input Validation** - All user inputs sanitized
- **CORS Protection** - Configured for specific origins
- **Database Security** - Parameterized queries prevent SQL injection
- **Error Handling** - Graceful error handling without exposing internals

## 🤝 Contributing

The dashboard is built with modularity in mind:
- **Add new charts** - Create new D3.js visualization functions
- **Extend API** - Add new Flask routes for additional data
- **Customize styling** - Modify CSS for different themes
- **Add features** - Extend ML models or add new predictions

## 📝 License

This project is part of the Drug Shortage Analysis system and follows the same licensing terms.

---

**Happy Analyzing! 🎯** 