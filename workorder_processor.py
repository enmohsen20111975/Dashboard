import pandas as pd
from datetime import datetime
import re

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
        
    # Fill NA values
    df = df.fillna('')
    
    # Combine description fields for classification
    df['combined_desc'] = df['WO_name'] + ' ' + df['Description']
    
    # Parse dates
    df['creation_date'] = df['Order_date'].combine_first(df['Start_dt']).apply(parse_excel_date)
    df['execution_date'] = df['Jobexec_dt'].apply(parse_excel_date)
    
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
    
    # Calculate time periods
    df['month'] = df['creation_date'].apply(get_month_from_date)
    df['quarter'] = df['creation_date'].apply(get_quarter_from_date)
    df['year'] = df['creation_date'].apply(get_year_from_date)
    
    # Determine failure causes and snag locations
    df['failure_cause'] = df['combined_desc'].apply(classify_failure)
    df['snag_location'] = df['combined_desc'].apply(find_snag_location)
    
    # Add breakdown location (if available)
    df['breakdown_location'] = df.get('Location', 'Unknown')
    
    return df

# Example usage:
if __name__ == "__main__":
    # Load sample data
    sample_data = [
        {
            "WO_key": "WO001",
            "WO_name": "STS01 Repair",
            "Description": "Hoist brake issue",
            "ETATJOB": "exe",
            "Jobexec_dt": "2024-01-15",
            "Order_date": "2024-01-10",
            "Start_dt": "2024-01-12",
            "Equipement": "STS01"
        },
        {
            "WO_key": "WO002", 
            "WO_name": "SP01 Maintenance",
            "Description": "Telescopic fault",
            "ETATJOB": "ter",
            "Jobexec_dt": "2024-02-20",
            "Order_date": "2024-02-01",
            "Equipement": "SP01"
        }
    ]
    
    processed = process_workorders(sample_data)
    print(processed)
