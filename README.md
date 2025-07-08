# Drug Shortage Analysis

This project fetches drug shortage data from the FDA API and loads it into a PostgreSQL database for analysis.

## Files

- `pull_drug_shortage_data.py` - Fetches drug shortage data from the FDA API and saves to CSV
- `load_to_database.py` - Connects to PostgreSQL database and loads the CSV data
- `test_connection.py` - Tests database connectivity and diagnoses connection issues
- `fix_schema.py` - Fixes database schema issues (run this if you get column size errors)
- `show_schema.py` - Shows the current database schema and sample data
- `requirements.txt` - Python dependencies
- `.env` - Database credentials (you need to create this)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your database credentials:
   ```
   DB_HOST=your_rds_endpoint
   DB_PORT=5432
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=your_database_name
   ```
   
   Example `.env` file:
   ```
   DB_HOST=db-drug-shortage-analysis.czowmakq697y.us-east-2.rds.amazonaws.com
   DB_PORT=5432
   DB_USER=mikec2611
   DB_PASSWORD=your_actual_password
   DB_NAME=postgres
   ```

   **⚠️ Important Note about Database Names:**
   - `DB_HOST` should be your RDS endpoint (e.g., `db-drug-shortage-analysis.czowmakq697y.us-east-2.rds.amazonaws.com`)
   - `DB_NAME` should be the actual database name inside your RDS instance, **not** the RDS instance name
   - Most AWS RDS PostgreSQL instances have a default database called `postgres`

## Usage

### 1. Test Database Connection (Recommended First Step)
```bash
python test_connection.py
```
This will test your database connection and provide detailed error messages if there are issues.

### 2. Fetch Drug Shortage Data
```bash
python pull_drug_shortage_data.py
```
This will create a `drug_shortages.csv` file with the latest FDA drug shortage data.

### 3. Fix Database Schema (If Needed)
If you encounter column size errors, run this first:
```bash
python fix_schema.py
```
This will drop and recreate the database table with the correct column sizes.

### 4. Load Data to Database
```bash
python load_to_database.py
```
This will load the CSV data into your PostgreSQL database.

## Troubleshooting

### Common Issues:

1. **Connection Timeout**: 
   - Check if your RDS security group allows connections from your IP
   - Verify the database endpoint is correct

2. **Authentication Failed**:
   - Verify your username and password in the `.env` file
   - Check if the database user has the necessary permissions

3. **Database Does Not Exist**:
   - Make sure `DB_NAME` in your `.env` file is the actual database name, not the RDS instance name
   - Try using `postgres` as the database name (default for most RDS instances)

4. **Column Size Errors**:
   - Run `python fix_schema.py` to fix the database schema
   - This will drop and recreate the table with appropriate column sizes
   - The updated schema handles long values like extensive drug names, complex strengths, and detailed pharmaceutical information

### Recent Fix (January 2025):
- **Fixed column size issues**: Updated database schema to handle real-world data lengths
- **Simplified schema**: Removed all OpenFDA fields (openfda.*) for a cleaner, more focused dataset
- **Key changes**: 
  - Focused on core drug shortage information only
  - `related_info_link` now uses TEXT (unlimited length)
  - Fields like `strength`, `presentation` now use VARCHAR(500)
  - Other fields sized appropriately based on actual FDA data analysis

### Security Notes:
- Never commit your `.env` file to version control
- Use strong passwords for your database
- Consider using IAM authentication for enhanced security
- Restrict database access to specific IP addresses in your security group

## Data Structure

The script creates a table called `drug_shortage_data` with the following columns:
- `id` - Primary key (auto-increment)
- `update_type` - Type of update (e.g., "Reverified")
- `initial_posting_date` - When the shortage was first posted
- `proprietary_name` - Brand name of the drug
- `strength` - Drug strength/concentration
- `package_ndc` - National Drug Code for the package
- `generic_name` - Generic name of the drug  
- `contact_info` - Contact information for inquiries
- `availability` - Availability status and details
- `update_date` - When the record was last updated
- `therapeutic_category` - Medical categories (e.g., "Cardiology")
- `dosage_form` - Form of the drug (e.g., "Tablet", "Injection")
- `presentation` - Detailed presentation information
- `company_name` - Manufacturer/company name
- `status` - Current status (e.g., "Current")
- `related_info` - Additional related information
- `shortage_reason` - Reason for the shortage
- `change_date` - Date of any changes
- `related_info_link` - Links to additional information
- `created_at` - When the record was inserted into the database
- `updated_at` - When the record was last modified

**Note**: OpenFDA fields have been removed for a cleaner, more focused dataset.

## Example Workflow

1. **First time setup**:
   ```bash
   pip install -r requirements.txt
   # Create .env file with your credentials
   python test_connection.py
   python pull_drug_shortage_data.py
   python fix_schema.py  # Only if you get column size errors
   python load_to_database.py
   ```

2. **Regular updates**:
   ```bash
   python pull_drug_shortage_data.py
   python load_to_database.py
   ```

## Database Schema

The database contains core drug shortage information from the FDA:
- Host: `db-drug-shortage-analysis.czowmakq697y.us-east-2.rds.amazonaws.com`
- Port: `5432`
- Database: Value from `.env` file (`DB_NAME`)
- Credentials: Values from `.env` file (`DB_USER` and `DB_PASSWORD`)

## Troubleshooting

If you get connection timeout errors, it's usually due to:

1. **RDS Security Group**: Your IP address might not be allowed to connect
2. **Public Access**: Your RDS database might not be publicly accessible
3. **VPC Configuration**: Database might be in a private subnet

Run `python test_connection.py` for detailed diagnostics.

## Example Usage

```bash
# Step 1: Test database connection
python test_connection.py

# Step 2: Fetch latest data
python pull_drug_shortage_data.py

# Step 3: Load into database
python load_to_database.py

# Step 4: View database schema and data
python show_schema.py
```

## Notes

- The loading script clears existing data and replaces it with fresh data each time it runs
- Make sure you have the `drug_shortages.csv` file before running the database loader
- The script includes comprehensive error handling and logging
- OpenFDA fields have been removed to focus on core drug shortage information
- Your `.env` file should not be committed to version control (add it to `.gitignore`)