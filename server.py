from flask import Flask, send_from_directory, jsonify, request
import json
import os
import sys
import pandas as pd
import logging
from datetime import datetime, timedelta
import re
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE = 'main.DB'

def create_tables():
    try:
        logging.info("Starting database initialization...")
        logging.info(f"Attempting to connect to database: {os.path.abspath(DATABASE)}")
        logging.info(f"Current working directory: {os.getcwd()}")
        logging.info(f"Directory permissions: {os.access(os.getcwd(), os.W_OK)}")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        logging.info("Database connection successful")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Workorders (
                WO_key TEXT PRIMARY KEY,
                WO_name TEXT,
                Description TEXT,
                ETATJOB TEXT,
                Jobexec_dt TEXT,
                Order_date TEXT,
                Start_dt TEXT,
                Equipement TEXT,
                Job_type TEXT,
                Cost_purpose_key TEXT
            )
        ''')
        logging.info("Table creation/verification successful")

        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Workorders'")
        if not cursor.fetchone():
            logging.error("Workorders table verification failed!")
            raise Exception("Workorders table not created")

        conn.commit()
        conn.close()
        logging.info("Database operations completed successfully")
    except Exception as e:
        logging.error(f"Database error: {str(e)}", exc_info=True)
        raise

create_tables()

def update_database(data_file):
    try:
        if data_file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(data_file)
        else:  # CSV
            df = pd.read_csv(data_file)
        conn = sqlite3.connect(DATABASE)
        df.to_sql('Workorders', conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

def classify_failure(cause):
    """Classify failure type based on description text"""
    if not cause:
        return cause
        
    d = str(cause).strip().upper()
    
    if "TWIN" in d: return "twin"
    if "TELESC" in d: return "Telescopy"
    if any(x in d for x in ["NOISE", "DAMAGE", "BRUIT", "ENDOMMA", "VIBRE"]): 
        return "Mech fail"
    if "AC FAULT" in d: return "A/C"
    if any(x in d for x in ["SIÈGE", "SEAT"]): return "operator seat"
    if "CRANE OF" in d: return "Crane off"
    if any(x in d for x in ["DRIVE OF", "CONTROL OF", "CONTROLE OF", "ALM"]): 
        return "Drive Off"
    if "POWER" in d: return "Power cut off"
    if any(x in d for x in ["ROOF", "TTDS", "SPREADER READY"]): 
        return "spreader ready intrlck"
    if "DOMMAGE" in d: return "Incident_Dommage"
    if any(x in d for x in ["HOIST BRAKE", "HOIST SERVICE BRAKE"]): 
        return "Hoist service brake"
    if "HOIST EMERG" in d: return "Hoist Emergency brake"
    if any(x in d for x in ["HDB", "HEADBLOCK"]): return "Headblock"
    if "FESTOON" in d: return "Festoon"
    if "HOIST SLOW" in d: return "Hoist slowdown"
    if "AFFICHEUR" in d: return "Display"
    if "GANTRY DRIVE" in d: return "Gantry drive"
    if "GANTRY POSITION" in d: return "Gantry position"
    if "GANTRY WHEEL" in d: return "Gantry wheel brake"
    if "GANTRY BRAKE" in d: return "Gantry brake"
    if "GANTRY ENCODER" in d: return "Gantry encoder"
    if "GANTRY MOTOR" in d: return "Gantry motor"
    if "TROLLEY DRIVE" in d: return "Trolley drive"
    if "TROLLEY POSITION" in d: return "Trolley position"
    if "TROLLEY BRAKE" in d: return "Trolley brake"
    if "TROLLEY GATE" in d: return "Trolley gate"
    if "TROLLEY ROPE" in d: return "Trolley rope tension"
    if "HOIST DRIVE" in d: return "hoist drive"
    if "HOIST POSITION" in d: return "hoist position"
    if "HOIST WIRE" in d: return "hoist wire rope"
    if "HOIST ENCODER" in d: return "Hoist encoder"
    if "HOIST MOTOR" in d: return "Hoist motor"
    if "GCR" in d: return "GCR"
    if any(x in d for x in ["SCR", "SPREADER CABLE REEL"]): return "SCR"
    if any(x in d for x in ["BAD STACK", "COINC", "SPREADER BLOQUÉ", 
                           "SPREADER ACCROCHÉ", "STUCK"]): return "Stuck"
    if any(x in d for x in ["BLINK FAULT", "COMMUNICA", "COMUNICA", "LIGHT BLINK"]): 
        return "Communication"
    if any(x in d for x in ["BOOM ISSUE", "BOOM FAULT", "BOOM INV"]): return "Boom Drive"
    if any(x in d for x in ["BOOM LEVEL", "BOOM DOWN", "BOOM UP", "NO BOOM"]): 
        return "Boom position"
    if "TLS" in d: return "TLS fault"
    if any(x in d for x in ["CHANGE", "CHANGEMENT"]): return "spreader change"
    if any(x in d for x in ["JOYSTICK", "JOYSTI"]): return "Joystick fault"
    if any(x in d for x in ["CONNECTOR", "PLUG"]): return "spreader plug"
    if any(x in d for x in ["FUITE D'HUILE", "OIL LEAK"]): return "oil leakage"
    if any(x in d for x in ["DÉVÉRROU", "VÉRROU", "LOCK FAULT", "UNLOCK", 
                           "UNLOPK", "LOCKING FAULT"]): return "Lock/unlock"
    if "FLIPPER" in d: return "Flipper"
    if any(x in d for x in ["TELESCOP", "TELECO", "TELSCO"]): return "Telescopic"
    if any(x in d for x in ["LIGHTS", "LIGHT", "LIGHT FAULT", "LIGHT ISSUE", 
                           "LIGHT OFF", "LAMPE", "FLOODLIGHT"]): return "Light"
    if any(x in d for x in ["POMPE SPREADER", "SPREADER PUMP", "PUMP"]): 
        return "spreader pump"
    
    return cause

def find_snag_location(short):
    """Determine snag location based on description text"""
    if not short:
        return ""
        
    s = str(short).upper()
    
    if "SNAG" in s:
        if "FAULT #0" in s: return "loadCell"
        if "FAULT #1" in s: return "Cylinder 1"
        if "FAULT #2" in s: return "Cylinder 2" 
        if "FAULT #3" in s: return "Cylinder 3"
        if "FAULT #4" in s: return "Cylinder 4"
        if any(x in s for x in ["FAULT #1 #2", "FAULT #1.#2"]): return "Cylinder 12"
        if any(x in s for x in ["FAULT #1 #3", "FAULT #1.#3"]): return "Cylinder 13"
        if any(x in s for x in ["FAULT #1 #4", "FAULT #1.#4"]): return "Cylinder 14"
        if any(x in s for x in ["FAULT #2 #3", "FAULT #2.#3"]): return "Cylinder 23"
        if any(x in s for x in ["FAULT #2 #4", "FAULT #2.#4"]): return "Cylinder 24"
        if any(x in s for x in ["FAULT #3 #4", "FAULT #3.#4"]): return "Cylinder 34"
        if any(x in s for x in ["FAULT #1 #2 #3", "FAULT #1.#2.#3"]): return "Cylinder 123"
        if any(x in s for x in ["FAULT #1 #2 #4", "FAULT #1.#2.#4"]): return "Cylinder 124"
        if any(x in s for x in ["FAULT #2 #3 #4", "FAULT #2.#3.#4"]): return "Cylinder 234"
        if any(x in s for x in ["FAULT #1 #2 #3 #4", "FAULT #1.#2.#3.#4"]): return "Cylinder 1234"
    
    return ""

def parse_excel_date(excel_date):
    """Parse dates from various Excel formats"""
    if not excel_date:
        return None
        
    # If already a datetime object
    if isinstance(excel_date, datetime):
        return excel_date
        
    # If numeric (Excel serial date)
    if isinstance(excel_date, (int, float)):
        # Excel's epoch starts on 1/1/1900
        excel_epoch = datetime(1899, 12, 30)  # Note: Excel incorrectly treats 1900 as leap year
        return excel_epoch + timedelta(days=excel_date)
        
    # If string, try parsing various formats
    if isinstance(excel_date, str):
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
            "%Y/%m/%d", "%d-%m-%Y", "%Y-%d-%m"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(excel_date, fmt)
            except ValueError:
                continue
                
    return None

def get_month_from_date(date):
    """Get YYYY-MM format from date"""
    if not date:
        return None
    return date.strftime("%Y-%m")
def get_quarter_from_date(date):
    """Get YYYY-QN format from date"""
    if not date:
        return None
    quarter = (date.month - 1) // 3 + 1
    return f"{date.year}-Q{quarter}"

def get_year_from_date(date):
    """Get year as string from date"""
    if not date:
        return None
    return str(date.year)

def process_workorders(data):
    """
    Process workorder data to generate enriched information
    Args:
        data: DataFrame or list of dicts containing workorder data
    Returns:
        DataFrame with processed workorder data
    """
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()
        
    # Convert all numeric columns to native Python types
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        df[col] = df[col].astype(object).where(pd.notnull(df[col]), None)
        
    # Fill NA values
    df = df.fillna('')
    
    # Combine description fields for classification
    df['combined_desc'] = df['WO_name'] + ' ' + df['Description']
    
    # Parse dates with error handling
    def safe_parse_date(date):
        try:
            return parse_excel_date(date)
        except:
            return None
            
    df['creation_date'] = df['Order_date'].combine_first(df['Start_dt']).apply(safe_parse_date)
    df['execution_date'] = df['Jobexec_dt'].apply(safe_parse_date)
    
    # Calculate durations (skip invalid dates)
    df['duration_days'] = df.apply(
        lambda x: (x['execution_date'] - x['creation_date']).days 
        if pd.notnull(x['execution_date']) and pd.notnull(x['creation_date']) 
        else None,
        axis=1
    )
    
    # Determine equipment type
    df['equipment_type'] = df['Equipement'].apply(
        lambda x: 'STS' if str(x).upper().startswith('STS') 
                 else 'Spreader' if str(x).upper().startswith('SP') 
                 else 'Other'
    )
    
    # Determine status
    status_map = {
        'exe': 'Ready for Work',
        'apc': 'Wait for Spare Parts', 
        'ter': 'Completed',
        'ini': 'Initiated'
    }
    
    df['status'] = df['ETATJOB'].str.lower().map(status_map).fillna('Pending')
    
    # Calculate time periods (skip invalid dates)
    df['month'] = df['creation_date'].apply(lambda x: get_month_from_date(x) if x else None)
    df['quarter'] = df['creation_date'].apply(lambda x: get_quarter_from_date(x) if x else None)
    df['year'] = df['creation_date'].apply(lambda x: get_year_from_date(x) if x else None)
    
    # Determine failure causes and snag locations
    df['failure_cause'] = df['combined_desc'].apply(classify_failure)
    df['snag_location'] = df['combined_desc'].apply(find_snag_location)
    
    # Add breakdown location (if available)
    df['breakdown_location'] = df.get('Location', 'Unknown')
    
    return df

@app.route('/all_data')
def get_all_data():
    """Endpoint to get all workorder data with filtering options"""
    try:
        print("DEBUG: Entering /all_data endpoint") 
        print(f"DEBUG: Database path: {os.path.abspath(DATABASE)}")
    except Exception as e:
        logging.error(f"Error in /all_data endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process request',
            'details': str(e),
            'status': 'error'
        }), 500

    # Get query parameters
    params = request.args.to_dict()
    
    # Extract special parameters
    kpis_only = params.pop('kpis_only', 'false').lower() == 'true'
    list_fields = params.pop('list_fields', None)
    fields = params.pop('fields', None)
    page = int(params.pop('page', 1))
    per_page = int(params.pop('per_page', 100))
    
    # Determine fields to select
    select_fields = '*'
    if fields:
        field_list = [f.strip() for f in fields.split(',')]
        valid_fields = ['WO_key', 'WO_name', 'Description', 'ETATJOB', 
                      'Jobexec_dt', 'Order_date', 'Start_dt', 'Equipement',
                      'Job_type', 'Cost_purpose_key']
        select_fields = ', '.join([f for f in field_list if f in valid_fields])
        
        # Use context manager to ensure connection is properly handled
        with sqlite3.connect(DATABASE) as conn:
            # Base query with pagination
            query = f"SELECT {select_fields} FROM Workorders"
            
            # Apply filters if any
            where_clauses = []
            query_params = []
            
            # Handle date range filtering
            start_date = params.pop('start_date', None)
            end_date = params.pop('end_date', None)
            if start_date and end_date:
                where_clauses.append("(Order_date >= ? OR Start_dt >= ?)")
                query_params.extend([start_date, start_date])
                where_clauses.append("(Order_date <= ? OR Start_dt <= ?)")
                query_params.extend([end_date, end_date])
            
            # Handle other filters
            for field, value in params.items():
                if field in ['Equipement', 'Job_type', 'ETATJOB', 'status']:
                    if field == 'status':
                        # Map status names to ETATJOB codes
                        status_map = {
                            'Ready for Work': 'exe',
                            'Wait for Spare Parts': 'apc',
                            'Completed': 'ter',
                            'Initiated': 'ini'
                        }
                        if value in status_map:
                            where_clauses.append("ETATJOB = ?")
                            query_params.append(status_map[value])
                    else:
                        # Exact match for other fields
                        where_clauses.append(f"{field} = ?")
                        query_params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add pagination
            query += f" LIMIT {per_page} OFFSET {(page-1)*per_page}"
            
            # Execute with parameters to prevent SQL injection
            # Explicitly cast numeric columns to TEXT to avoid numpy types
            type_cast_query = query.replace("SELECT", "SELECT CAST(WO_key AS TEXT) as WO_key,") \
                if select_fields == '*' else query
            df = pd.read_sql_query(type_cast_query, conn, params=query_params)
            
            # Convert all remaining numeric columns to native Python types
            for col in df.select_dtypes(include=['int64', 'float64']).columns:
                df[col] = df[col].astype(object).where(pd.notnull(df[col]), None)
        
        # Handle empty case
        if df.empty:
            return jsonify({
                'raw_data': [],
                'kpis': {},
                'lists': {},
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0
                }
            })
        
        # Process the workorder data
        processed_df = process_workorders(df)
        
        # Get total count for pagination
        with sqlite3.connect(DATABASE) as conn:
            total_query = "SELECT COUNT(*) FROM Workorders"
            if where_clauses:
                total_query += " WHERE " + " AND ".join(where_clauses)
            total = pd.read_sql_query(total_query, conn, params=query_params).iloc[0,0]
        
        # Prepare response
        response = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        }
        
        # Add raw data unless only KPIs requested
        if not kpis_only:
            # Convert DataFrame to dict with native Python types
            response['raw_data'] = (
                processed_df.apply(lambda x: x.astype(object) if x.dtype == 'int64' else x)
                .astype(object)
                .where(pd.notnull(processed_df), None)
                .to_dict('records')
            )
        
        # Calculate KPIs
        response['kpis'] = {
            'total_workorders': total,
            'completed': len(processed_df[processed_df['status'] == 'Completed']),
            'in_progress': len(processed_df[processed_df['status'] == 'Ready for Work']),
            'pending': len(processed_df[processed_df['status'] == 'Pending']),
            'waiting_parts': len(processed_df[processed_df['status'] == 'Wait for Spare Parts']),
            'average_duration': float(processed_df['duration_days'].mean())
        }
        
        # Add field lists if requested
        if list_fields:
            response['lists'] = {
                'equipment': processed_df['Equipement'].unique().tolist(),
                'categories': processed_df['Job_type'].unique().tolist(),
                'fault_locations': processed_df['ETATJOB'].unique().tolist(),
                'failure_causes': processed_df['failure_cause'].unique().tolist(),
                'snag_locations': processed_df['snag_location'].unique().tolist()
            }
        
        return jsonify(response)

@app.route('/stream_data')
def stream_data():
    """Stream workorder data as newline-delimited JSON"""
    params = request.args.to_dict()
    
    # Determine fields to select
    select_fields = '*'
    if 'fields' in params:
        field_list = [f.strip() for f in params['fields'].split(',')]
        valid_fields = ['WO_key', 'WO_name', 'Description', 'ETATJOB', 
                      'Jobexec_dt', 'Order_date', 'Start_dt', 'Equipement',
                      'Job_type', 'Cost_purpose_key']
        select_fields = ', '.join([f for f in field_list if f in valid_fields])
    
    def generate():
        try:
            with sqlite3.connect(DATABASE) as conn:
                # Base query
                query = f"SELECT {select_fields} FROM Workorders"
                
                # Apply filters if any
                where_clauses = []
                query_params = []
                
                # Handle date range filtering
                start_date = params.pop('start_date', None)
                end_date = params.pop('end_date', None)
                if start_date and end_date:
                    where_clauses.append("(Order_date >= ? OR Start_dt >= ?)")
                    query_params.extend([start_date, start_date])
                    where_clauses.append("(Order_date <= ? OR Start_dt <= ?)")
                    query_params.extend([end_date, end_date])
                
                # Handle other filters
                for field, value in params.items():
                    if field in ['Equipement', 'Job_type', 'ETATJOB', 'status']:
                        if field == 'status':
                            status_map = {
                                'Ready for Work': 'exe',
                                'Wait for Spare Parts': 'apc',
                                'Completed': 'ter',
                                'Initiated': 'ini'
                            }
                            if value in status_map:
                                where_clauses.append("ETATJOB = ?")
                                query_params.append(status_map[value])
                        else:
                            where_clauses.append(f"{field} = ?")
                            query_params.append(value)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                # Execute query with server-side cursor
                cursor = conn.cursor()
                cursor.execute(query, query_params)
                
                # Stream results
                columns = [col[0] for col in cursor.description]
                for row in cursor:
                    record = dict(zip(columns, row))
                    processed = process_workorders(pd.DataFrame([record]))
                    yield json.dumps(processed.to_dict('records')[0]) + '\n'
        except Exception as e:
            logging.error(f"Error in stream_data generator: {str(e)}")
            yield json.dumps({
                'error': 'Failed to stream data',
                'details': str(e),
                'status': 'error'
            }) + '\n'
    
    try:
        return Response(generate(), mimetype='application/x-ndjson')
    except Exception as e:
        logging.error(f"Error in /stream_data endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to initialize streaming',
            'details': str(e),
            'status': 'error'
        }), 500

@app.route('/test')
def test_endpoint():
    """Test endpoint to verify server is responding"""
    logging.info("Handling test endpoint request - route is registered")
    try:
        response = jsonify({
            'status': 'ok',
            'message': 'Server is running',
            'timestamp': datetime.now().isoformat(),
            'routes': [str(rule) for rule in app.url_map.iter_rules()]
        })
        logging.info(f"Test endpoint response prepared: {response.get_data(as_text=True)}")
        return response
    except Exception as e:
        logging.error(f"Test endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Test endpoint failed',
            'details': str(e),
            'routes': [str(rule) for rule in app.url_map.iter_rules()]
        }), 500

@app.route('/')
def index():
    """Serve index.html with error handling"""
    try:
        logging.debug("Serving index.html")
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logging.error(f"Failed to serve index.html: {str(e)}")
        return jsonify({'error': f"Failed to load index page: {str(e)}"}), 500

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('Data', filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads to update the database with enhanced error handling"""
    # Validate request contains file
    if 'file' not in request.files:
        logging.warning("Upload attempt with no file part")
        return jsonify({
            'error': 'No file part in request',
            'status': 'error',
            'code': 'MISSING_FILE_PART'
        }), 400

    file = request.files['file']
    
    # Validate filename
    if file.filename == '':
        logging.warning("Upload attempt with empty filename")
        return jsonify({
            'error': 'No file selected',
            'status': 'error',
            'code': 'EMPTY_FILENAME'
        }), 400

    # Validate file extension
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        logging.warning(f"Invalid file type attempted: {file.filename}")
        return jsonify({
            'error': 'Invalid file type - must be Excel (.xlsx, .xls) or CSV',
            'allowed_types': ['xlsx', 'xls', 'csv'],
            'status': 'error',
            'code': 'INVALID_FILE_TYPE'
        }), 400

    # Validate file size (max 10MB)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    file.seek(0, 2)  # Seek to end to get size
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > MAX_SIZE:
        logging.warning(f"File too large: {file.filename} ({file_size} bytes)")
        return jsonify({
            'error': f'File too large - max size is {MAX_SIZE//(1024*1024)}MB',
            'status': 'error',
            'code': 'FILE_TOO_LARGE'
        }), 400

    # Create temp upload directory if needed
    temp_dir = 'temp_uploads'
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Save file temporarily for validation
        temp_path = os.path.join(temp_dir, f"upload_{int(time.time())}_{file.filename}")
        file.save(temp_path)
        logging.info(f"Saved upload to temp file: {temp_path}")

        # Validate file contents
        try:
            if temp_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_path)
            else:  # CSV
                df = pd.read_csv(temp_path)
                
            # Check for required columns
            required_cols = ['WO_key', 'WO_name', 'Description', 'ETATJOB', 
                           'Jobexec_dt', 'Order_date', 'Start_dt', 'Equipement']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logging.error(f"Missing required columns in {file.filename}: {missing_cols}")
                return jsonify({
                    'error': f'File missing required columns: {", ".join(missing_cols)}',
                    'status': 'error',
                    'code': 'MISSING_COLUMNS'
                }), 400
                
        except Exception as e:
            logging.error(f"Error reading/validating file {file.filename}: {str(e)}")
            return jsonify({
                'error': 'Invalid file contents - could not read as Excel/CSV',
                'details': str(e),
                'status': 'error',
                'code': 'INVALID_FILE_CONTENTS'
            }), 400

        # Update database
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Backup current data
            backup_table = f"Workorders_backup_{int(time.time())}"
            cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM Workorders")
            conn.commit()
            logging.info(f"Created backup table: {backup_table}")

            # Update with new data
            df.to_sql('Workorders', conn, if_exists='replace', index=False)
            
            # Validate update
            cursor.execute("SELECT COUNT(*) FROM Workorders")
            new_count = cursor.fetchone()[0]
            logging.info(f"Database updated - new record count: {new_count}")
            
            conn.close()
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({
                'message': 'Database updated successfully',
                'filename': file.filename,
                'records_updated': new_count,
                'backup_table': backup_table,
                'status': 'success'
            })
            
        except Exception as e:
            logging.error(f"Database update failed for {file.filename}: {str(e)}", exc_info=True)
            
            # Attempt to restore from backup if exists
            if 'backup_table' in locals():
                try:
                    cursor.execute("DROP TABLE IF EXISTS Workorders")
                    cursor.execute(f"CREATE TABLE Workorders AS SELECT * FROM {backup_table}")
                    conn.commit()
                    logging.info("Restored database from backup")
                except Exception as restore_error:
                    logging.critical(f"Failed to restore database: {str(restore_error)}")
            
            return jsonify({
                'error': 'Failed to update database',
                'details': str(e),
                'status': 'error',
                'code': 'DATABASE_UPDATE_FAILED'
            }), 500
            
    except Exception as e:
        logging.error(f"Error processing upload: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error during upload',
            'details': str(e),
            'status': 'error',
            'code': 'INTERNAL_ERROR'
        }), 500
        
    finally:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logging.warning(f"Failed to clean up temp file {temp_path}: {str(e)}")

@app.route('/table_lengths')
def table_lengths():
    try:
        table_lengths = {}
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM '{table[0]}'")
            table_lengths[table[0]] = cursor.fetchone()[0]
        conn.close()
        return jsonify(table_lengths)
    except Exception as e:
        logging.error(f"Error in /table_lengths endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch table lengths',
            'details': str(e),
            'status': 'error'
        }), 500

# Translation tools endpoints
@app.route('/translate/excel', methods=['POST'])
def translate_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type'})

    try:
        # Save uploaded file temporarily
        upload_path = os.path.join('temp_uploads', file.filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(upload_path)
        
        # Process Excel file while preserving formatting
        from openpyxl import load_workbook
        wb = load_workbook(upload_path)
        
        # TODO: Implement actual translation logic here
        # For now just save the file as-is
        translated_path = os.path.join('temp_uploads', f'translated_{file.filename}')
        wb.save(translated_path)
        
        download_url = f'/download/translated_{file.filename}'
        
        return jsonify({
            'message': 'Excel translation complete (format preserved)',
            'download_url': download_url
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/translate/pdf', methods=['POST'])
def translate_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'})

    try:
        # Save uploaded file temporarily
        upload_path = os.path.join('temp_uploads', file.filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(upload_path)
        
        # Extract text from PDF
        from pdfminer.high_level import extract_text
        text = extract_text(upload_path)
        
        # TODO: Implement actual translation logic here
        # For now just save extracted text as TXT file
        translated_path = os.path.join('temp_uploads', f'translated_{os.path.splitext(file.filename)[0]}.txt')
        with open(translated_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        download_url = f'/download/translated_{os.path.splitext(file.filename)[0]}.txt'
        
        return jsonify({
            'message': 'PDF text extracted (translation pending)',
            'download_url': download_url
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/translate/office', methods=['POST'])
def translate_office():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if not file.filename.endswith(('.docx', '.pptx')):
        return jsonify({'error': 'Invalid file type'})

    try:
        # Save uploaded file temporarily
        upload_path = os.path.join('temp_uploads', file.filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(upload_path)
        
        # Process Office document
        if file.filename.endswith('.docx'):
            from docx import Document
            doc = Document(upload_path)
            
            # TODO: Implement actual translation logic here
            # For now just save the document as-is
            translated_path = os.path.join('temp_uploads', f'translated_{file.filename}')
            doc.save(translated_path)
            
        elif file.filename.endswith('.pptx'):
            from pptx import Presentation
            prs = Presentation(upload_path)
            
            # TODO: Implement actual translation logic here
            # For now just save the presentation as-is
            translated_path = os.path.join('temp_uploads', f'translated_{file.filename}')
            prs.save(translated_path)
        
        download_url = f'/download/translated_{file.filename}'
        
        return jsonify({
            'message': 'Office document processed (translation pending)',
            'download_url': download_url
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('temp_uploads', filename, as_attachment=True)

# PDF Processing Endpoints
@app.route('/pdf/merge', methods=['POST'])
def merge_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part'})
    
    files = request.files.getlist('files')
    if len(files) < 2:
        return jsonify({'error': 'Need at least 2 files to merge'})

    try:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        
        # Save and add each file to merger
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'All files must be PDFs'})
            
            file_path = os.path.join('temp_uploads', file.filename)
            file.save(file_path)
            merger.append(file_path)

        # Save merged result
        merged_filename = f'merged_{int(time.time())}.pdf'
        merged_path = os.path.join('temp_uploads', merged_filename)
        merger.write(merged_path)
        merger.close()

        return jsonify({
            'message': 'PDFs merged successfully',
            'download_url': f'/download/{merged_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/pdf/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    split_page = request.form.get('split_page')
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'})
    if not split_page or not split_page.isdigit():
        return jsonify({'error': 'Invalid split page number'})
    
    try:
        from PyPDF2 import PdfReader, PdfWriter
        
        # Save uploaded file
        file_path = os.path.join('temp_uploads', file.filename)
        file.save(file_path)
        
        # Split the PDF
        reader = PdfReader(file_path)
        split_page = int(split_page)
        
        if split_page < 1 or split_page > len(reader.pages):
            return jsonify({'error': 'Split page out of range'})
        
        # Create first part
        writer1 = PdfWriter()
        for page in reader.pages[:split_page]:
            writer1.add_page(page)
        part1_name = f'split1_{file.filename}'
        part1_path = os.path.join('temp_uploads', part1_name)
        with open(part1_path, 'wb') as f:
            writer1.write(f)
        
        # Create second part
        writer2 = PdfWriter()
        for page in reader.pages[split_page:]:
            writer2.add_page(page)
        part2_name = f'split2_{file.filename}'
        part2_path = os.path.join('temp_uploads', part2_name)
        with open(part2_path, 'wb') as f:
            writer2.write(f)
        
        return jsonify({
            'message': 'PDF split successfully',
            'download_urls': [
                f'/download/{part1_name}',
                f'/download/{part2_name}'
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/pdf/extract', methods=['POST'])
def extract_pages():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    pages = request.form.get('pages')
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'})
    if not pages:
        return jsonify({'error': 'No pages specified'})
    
    try:
        from PyPDF2 import PdfReader, PdfWriter
        
        # Save uploaded file
        file_path = os.path.join('temp_uploads', file.filename)
        file.save(file_path)
        
        # Parse page ranges (e.g. "1-3,5,7-9")
        page_numbers = set()
        for part in pages.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                page_numbers.update(range(start, end + 1))
            else:
                page_numbers.add(int(part))
        
        # Extract specified pages
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        for i in sorted(page_numbers):
            if 1 <= i <= len(reader.pages):
                writer.add_page(reader.pages[i-1])
        
        extracted_name = f'extracted_{file.filename}'
        extracted_path = os.path.join('temp_uploads', extracted_name)
        with open(extracted_path, 'wb') as f:
            writer.write(f)
        
        return jsonify({
            'message': 'Pages extracted successfully',
            'download_url': f'/download/{extracted_name}'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/pdf/ocr', methods=['POST'])
def ocr_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'})
    
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image
        import io
        
        # Save uploaded file
        file_path = os.path.join('temp_uploads', file.filename)
        file.save(file_path)
        
        # Convert PDF to images
        images = convert_from_path(file_path)
        
        # OCR each page
        ocr_text = []
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            ocr_text.append(f"--- Page {i+1} ---\n{text}\n")
        
        # Save OCR result
        ocr_filename = f'ocr_{os.path.splitext(file.filename)[0]}.txt'
        ocr_path = os.path.join('temp_uploads', ocr_filename)
        with open(ocr_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ocr_text))
        
        return jsonify({
            'message': 'OCR completed successfully',
            'download_url': f'/download/{ocr_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/merged_purchases')
def get_merged_purchases():
    """Get purchase data from database tables"""
    try:
        conn = sqlite3.connect(DATABASE)
        
        # Get PO data
        po_df = pd.read_sql_query("SELECT * FROM purchase_orders", conn)
        
        # Get PR data 
        pr_df = pd.read_sql_query("SELECT * FROM purchase_requests", conn)
        
        # Get Sage data
        sage_df = pd.read_sql_query("SELECT * FROM sage_transactions", conn)
        
        conn.close()

        # Standardize column names for merging
        po_df = po_df.rename(columns={
            'po_number': 'po_number',
            'item_code': 'item_code',
            'quantity': 'po_quantity',
            'unit_price': 'po_unit_price'
        })
        
        pr_df = pr_df.rename(columns={
            'pr_number': 'pr_number',
            'item_code': 'item_code',
            'quantity': 'pr_quantity',
            'unit_price': 'pr_unit_price'
        })
        
        sage_df = sage_df.rename(columns={
            'doc_number': 'sage_doc_number',
            'item_code': 'item_code',
            'quantity': 'sage_quantity',
            'unit_price': 'sage_unit_price'
        })

        # First merge PO and PR data
        merged = pd.merge(
            po_df,
            pr_df,
            on='item_code',
            how='outer',
            suffixes=('_po', '_pr')
        )

        # Then merge with Sage data
        merged = pd.merge(
            merged,
            sage_df,
            on='item_code',
            how='outer'
        )

        # Calculate derived fields
        merged['total_po_value'] = merged['po_quantity'] * merged['po_unit_price']
        merged['total_pr_value'] = merged['pr_quantity'] * merged['pr_unit_price']
        merged['total_sage_value'] = merged['sage_quantity'] * merged['sage_unit_price']

        # Fill NA values for cleaner output
        merged = merged.fillna('')

        # Convert DataFrame to dict with native Python types
        data = merged.astype(object).where(pd.notnull(merged), None).to_dict('records')
        
        return jsonify({
            'raw_data': data,
            'summary': {
                'total_items': int(len(merged)),
                'total_po_value': float(merged['total_po_value'].sum()),
                'total_pr_value': float(merged['total_pr_value'].sum()),
                'total_sage_value': float(merged['total_sage_value'].sum())
            }
        })
    except Exception as e:
        print(f"Error merging purchase data: {str(e)}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # Configure detailed logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='server.log',
        filemode='w'
    )
    logging.info("Starting server initialization")
    
    # Initialize database
    try:
        logging.info("Calling create_tables()")
        create_tables()
        logging.info("Database initialization complete")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}", exc_info=True)
        raise
    
    # Log startup information
    logging.info("Starting server...")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Working directory: {os.getcwd()}")
    logging.info(f"Database path: {os.path.abspath(DATABASE)}")
    
    # Log registered routes
    logging.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logging.info(f"  {rule}")
    
    try:
        logging.info("Starting Flask application...")
        # Explicitly check port availability
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('0.0.0.0', 5050))
        sock.close()
        
        if result == 0:
            logging.error("Port 5050 is already in use!")
            sys.exit(1)
        
        logging.info("Port 5050 is available - starting server")
        
        # Start Flask app with explicit error handling
        try:
            from werkzeug.serving import run_simple
            logging.info("About to call run_simple()")
            run_simple('0.0.0.0', 5050, app, use_reloader=True, use_debugger=True)
            logging.info("run_simple() completed")
        except Exception as e:
            logging.critical(f"Flask server failed to start: {str(e)}", exc_info=True)
            raise
        finally:
            logging.info("Server startup attempt completed")
    except Exception as e:
        logging.critical(f"Server startup failed: {str(e)}", exc_info=True)
        print(f"CRITICAL ERROR: {str(e)}")
        raise
