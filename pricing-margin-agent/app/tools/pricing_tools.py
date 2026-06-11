"""Tools for the Smile Pricing & Margin Agent."""
from typing import Any, Dict, List, Optional
import os
import json

# Load mock database dynamically from mock_data.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(CURRENT_DIR, "mock_data.json")

MOCK_DB = {}
try:
    with open(JSON_PATH, "r") as f:
        MOCK_DB = json.load(f)
except Exception as e:
    # Fallback simple database in case of file load errors
    MOCK_DB = {
        "market_benchmarks": [
            {
                "role": "DevOps Engineer",
                "experience_years": 5,
                "location": "Lille",
                "average_tjm": 620,
                "min_tjm": 580,
                "max_tjm": 670
            }
        ],
        "client_historical_pricing": [
            {
                "client_name": "Decathlon",
                "role": "DevOps Engineer",
                "average_tjm_paid": 650,
                "notes": "Accepts a premium for Senior Cloud roles that accelerate their digital transformation."
            }
        ],
        "approvers": {
            "agency_director": "Thomas E. (Agency Director - Lille)",
            "sales_director": "Sophie M. (Sales Director - Retail & E-commerce)"
        }
    }

def get_market_benchmarks(role: str, experience_years: int, location: str) -> Dict[str, Any]:
    """Fetch external market average TJM (daily rate) for a specific role, experience, and location.

    Args:
        role: The candidate's job role (e.g., 'DevOps Engineer', 'Magento Developer', 'Magento Tech Lead', 'Drupal Expert').
        experience_years: Years of professional experience.
        location: The geographical location (e.g., 'Lille', 'Paris').

    Returns:
        A dictionary containing average_tjm, min_tjm, max_tjm, and search details.
    """
    benchmarks = MOCK_DB.get("market_benchmarks", [])
    
    # Try exact match first
    for b in benchmarks:
        if (b["role"].lower() == role.lower() and 
            b["experience_years"] == experience_years and 
            b["location"].lower() == location.lower()):
            return {
                "role": role,
                "experience_years": experience_years,
                "location": location,
                "average_tjm": b["average_tjm"],
                "min_tjm": b["min_tjm"],
                "max_tjm": b["max_tjm"],
                "source": "Smile External Market Intelligence Database"
            }

    # Fuzzy match or general fallback if exact match is missing
    matching_roles = [b for b in benchmarks if role.lower() in b["role"].lower()]
    if matching_roles:
        # Sort by location match
        loc_match = [b for b in matching_roles if location.lower() in b["location"].lower()]
        match = loc_match[0] if loc_match else matching_roles[0]
        return {
            "role": role,
            "experience_years": experience_years,
            "location": location,
            "average_tjm": match["average_tjm"],
            "min_tjm": match["min_tjm"],
            "max_tjm": match["max_tjm"],
            "source": "Smile External Market Intelligence Database (Closest Match)"
        }

    # Absolute default values if nothing matches
    base_rate = 500 + (experience_years * 25)
    if location.lower() == "paris":
        base_rate += 100
    return {
        "role": role,
        "experience_years": experience_years,
        "location": location,
        "average_tjm": base_rate,
        "min_tjm": int(base_rate * 0.9),
        "max_tjm": int(base_rate * 1.1),
        "source": "Smile Dynamic Benchmark Estimator"
    }

def get_client_historical_pricing(client_name: str) -> List[Dict[str, Any]]:
    """Fetch data from internal Smile ERP/billing systems regarding historical TJM paid by a client.

    Args:
        client_name: The name of the client to look up (e.g., 'Decathlon', 'Auchan', 'Leroy Merlin').

    Returns:
        A list of dictionaries containing historical roles, average rates paid, and notes.
    """
    historical = MOCK_DB.get("client_historical_pricing", [])
    results = []
    
    for h in historical:
        if client_name.lower() in h["client_name"].lower():
            results.append({
                "client_name": h["client_name"],
                "role": h["role"],
                "average_tjm_paid": h["average_tjm_paid"],
                "notes": h["notes"],
                "source": "Smile ERP & Billing Historical Logs"
            })
            
    if not results:
        # Return a generic entry for a new client
        results.append({
            "client_name": client_name,
            "role": "All Digital Roles",
            "average_tjm_paid": 0,
            "notes": "No historical pricing logs found. Treat as a standard margin account.",
            "source": "Smile ERP"
        })
        
    return results

def calculate_project_profitability(salary_cost: float, proposed_tjm: float) -> Dict[str, Any]:
    """Calculate Gross Margin, Net Margin, Daily Cost, and recommended TJM base for a proposed rate.

    Args:
        salary_cost: The consultant's annual gross salary in Euros (e.g., 65000).
        proposed_tjm: The daily rate proposed to the client in Euros (e.g., 650).

    Returns:
        A dictionary breakdown of the profitability metrics.
    """
    # Convert annual salary to daily cost base (including ~31% social charges/taxes to make 65k salary match 390 daily cost base exactly)
    # 65000 * 1.3085 / 218 = 390
    social_charges_rate = 0.3085
    total_days = 218
    
    daily_cost_base = round((salary_cost * (1 + social_charges_rate)) / total_days, 2)
    
    # Operational overheads: internal costs of agencies (IT, support staff, offices) ~ 19.3% of daily cost base, i.e. ~€75.38
    overheads_rate = 0.193
    operational_overheads = round(daily_cost_base * overheads_rate, 2)
    
    total_daily_cost = daily_cost_base + operational_overheads
    
    # Profitability and Margins
    # Gross Margin = (proposed_tjm - daily_cost_base) / proposed_tjm
    if proposed_tjm > 0:
        gross_margin = round(((proposed_tjm - daily_cost_base) / proposed_tjm) * 100, 2)
        # Net Margin = (proposed_tjm - total_daily_cost) / proposed_tjm
        net_margin = round(((proposed_tjm - total_daily_cost) / proposed_tjm) * 100, 2)
    else:
        gross_margin = 0.0
        net_margin = 0.0

    # Sweet Spot recommended TJM for different target net margins
    # Formula: TJM = (Cost + Overheads) / (1 - Target Margin)
    sweet_spot_30 = round(total_daily_cost / (1 - 0.30), 2)
    sweet_spot_25 = round(total_daily_cost / (1 - 0.25), 2)
    sweet_spot_35 = round(total_daily_cost / (1 - 0.35), 2)
    sweet_spot_40 = round(total_daily_cost / (1 - 0.40), 2)

    return {
        "annual_salary": salary_cost,
        "daily_cost_base": daily_cost_base,
        "operational_overheads": operational_overheads,
        "total_daily_cost": total_daily_cost,
        "proposed_tjm": proposed_tjm,
        "gross_margin_percent": gross_margin,
        "net_margin_percent": net_margin,
        "sweet_spot_recommendations": {
            "25%_net_margin": sweet_spot_25,
            "30%_net_margin_target": sweet_spot_30,
            "35%_net_margin": sweet_spot_35,
            "40%_net_margin_scarcity": sweet_spot_40
        }
    }

def approve_discount_level(requested_tjm: float, floor_tjm: float) -> Dict[str, Any]:
    """Workflow tool simulating director approval if a requested TJM falls below the margin floor.

    Args:
        requested_tjm: The pricing rate being requested.
        floor_tjm: The minimum rate allowed to hit the floor target (usually 25% net margin).

    Returns:
        A dictionary containing approval status, approver names, and recommendations.
    """
    approvers = MOCK_DB.get("approvers", {
        "agency_director": "Thomas E. (Agency Director - Lille)",
        "sales_director": "Sophie M. (Sales Director - Retail & E-commerce)"
    })

    if requested_tjm >= floor_tjm:
        return {
            "approved": True,
            "status": "APPROVED",
            "message": f"The proposed TJM of €{requested_tjm} is equal to or above the minimum required floor TJM of €{floor_tjm}.",
            "authorized_by": "Auto-Approved (Within standard margin parameters)"
        }
    
    # Price is below floor
    discount_percentage = round(((floor_tjm - requested_tjm) / floor_tjm) * 100, 2)
    
    # Escalation rules
    if discount_percentage > 15:
        approver = approvers["sales_director"]
        action_required = "Escalate to Sales Director for strategic discount approval."
    else:
        approver = approvers["agency_director"]
        action_required = "Requires Agency Director validation for regional margin override."

    return {
        "approved": False,
        "status": "PENDING_DIRECTOR_APPROVAL",
        "discount_percentage": discount_percentage,
        "required_approver": approver,
        "floor_tjm": floor_tjm,
        "action_required": action_required,
        "message": f"Alert: Proposed TJM (€{requested_tjm}) falls {discount_percentage}% below the margin floor (€{floor_tjm}). Operational rules require official sign-off."
    }
