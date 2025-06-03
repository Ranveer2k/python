import streamlit as st # type: ignore
from PIL import Image # type: ignore
import io
import base64
import os
import requests # type: ignore
from tenacity import retry, stop_after_attempt, wait_exponential # type: ignore
from openai import OpenAI # type: ignore
import json
import pandas as pd # type: ignore

# === Configuration ===
# Use environment variables or Streamlit secrets for API keys
OPENROUTER_API_KEY = os.getenv("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") #or st.secrets.get("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemini-pro-vision"  # Using OpenRouter's vision model

# Initialize OpenRouter client
openrouter_client = None
if OPENROUTER_API_KEY:
    try:
        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
    except Exception as e:
        st.error(f"OpenRouter client initialization failed: {str(e)}")

# === Solar Industry Constants ===
SOLAR_PANEL_TYPES = {
    "Monocrystalline": {
        "efficiency": "15-22%",
        "cost_per_watt": 45,
        "lifespan": "25-30 years",
        "description": "High efficiency, space-efficient, more expensive"
    },
    "Polycrystalline": {
        "efficiency": "13-16%",
        "cost_per_watt": 40,
        "lifespan": "23-27 years",
        "description": "Good value, moderate efficiency"
    },
    "Thin-Film": {
        "efficiency": "10-13%",
        "cost_per_watt": 35,
        "lifespan": "10-20 years",
        "description": "Lightweight, flexible, lower efficiency"
    }
}

GOVERNMENT_INCENTIVES = {
    "India": {
        "Central Financial Assistance (CFA)": "Up to 40% subsidy for residential systems",
        "Net Metering": "Available in most states",
        "Tax Benefits": "Accelerated depreciation for commercial systems"
    },
    "USA": {
        "Federal Tax Credit": "26% of system cost (2023)",
        "State Incentives": "Varies by state",
        "Net Metering": "Available in most states"
    },
    "Germany": {
        "Feed-in Tariff": "Guaranteed rates for solar power",
        "VAT Reduction": "Reduced VAT for solar systems"
    }
}

# Default Electricity Rates and Sun Hours by Country
DEFAULT_SOLAR_PARAMS = {
    "India": {"electricity_rate": 0.12, "sun_hours": 4.5},
    "USA": {"electricity_rate": 0.15, "sun_hours": 5.1},
    "Germany": {"electricity_rate": 0.13, "sun_hours": 4.9},
}

# === Helper Functions ===
def resize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """Resize image to reduce API payload while maintaining aspect ratio"""
    try:
        width, height = image.size
        if width > max_size or height > max_size:
            ratio = min(max_size/width, max_size/height)
            new_size = (int(width * ratio), (int(height * ratio)))
            return image.resize(new_size, Image.LANCZOS)
        return image
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return image

def calculate_financials(panel_type, system_size, electricity_rate, sun_hours=4.5, country="India"):
    """Calculate financial metrics for solar installation"""
    try:
        cost_per_watt = SOLAR_PANEL_TYPES[panel_type]["cost_per_watt"]
        total_cost = system_size * cost_per_watt * 1000  # Convert kW to W
        annual_production = system_size * sun_hours * 365
        annual_savings = annual_production * electricity_rate
        roi_years = total_cost / annual_savings
        
        incentives = GOVERNMENT_INCENTIVES.get(country, {})
        
        return {
            "total_cost": total_cost,
            "annual_production_kwh": annual_production,
            "annual_savings": annual_savings,
            "roi_years": roi_years,
            "incentives": incentives
        }
    except Exception as e:
        st.error(f"Financial calculation error: {str(e)}")
        return None

# === AI Analysis Functions ===
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_rooftop_with_ai(image: Image.Image, country: str):
    """Analyze rooftop image with AI for solar potential"""
    try:
        # Prepare image
        image = resize_image(image)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        prompt = f"""You are a solar installation expert analyzing a rooftop in {country}. Provide a detailed analysis including:

1. **Rooftop Assessment**:
   - Usable area (square meters)
   - Orientation and tilt
   - Shading obstacles
   - Structural considerations

2. **Solar Potential**:
   - Recommended system size (kW)
   - Optimal panel type from {list(SOLAR_PANEL_TYPES.keys())}
   - Estimated annual production (kWh)

3. **Installation Details**:
   - Recommended mounting approach
   - Electrical considerations
   - Any permit requirements

4. **Financial Analysis**:
   - Estimated costs
   - ROI timeframe
   - Available incentives in {country}

5. **Maintenance Requirements**:
   - Cleaning frequency
   - Monitoring recommendations
   - Warranty information

Format as markdown with clear headings. Include quantitative estimates where possible."""

        if not openrouter_client:
            raise Exception("No API client available")

        response = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.secrets.get("SITE_URL", "https://solar-rooftop.streamlit.app"),
                "X-Title": "Solar Industry AI Assistant"
            },
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"API call failed: {str(e)}")
        raise

# === Streamlit UI ===
st.set_page_config(
    page_title="Solar Industry AI Assistant",
    layout="wide",
    page_icon="☀️"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1 {
        color: #2b5876;
    }
    .footer {
        font-size: 0.8rem;
        color: #6c757d;
        text-align: center;
        padding: 1rem;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .panel-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Main App
st.title("☀️ Solar Industry AI Assistant")
st.markdown("""
**Professional rooftop solar potential analysis tool**  
Upload satellite imagery or rooftop photos for comprehensive solar installation assessment.
""")

# API Status
# if not openrouter_client:
#     st.error("""
#     <div class="error-box">
#         <h4>API Configuration Required</h4>
#         <p>Please set OPENROUTER_API_KEY as environment variable or in Streamlit secrets.</p>
#     </div>
#     """, unsafe_allow_html=True)
#     st.stop()

# Main Columns
col1, col2 = st.columns([1, 1])

with col1:
    # Image Upload Section
    with st.expander("📷 Upload Rooftop Image", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a rooftop image (satellite or direct photo)",
            type=["png", "jpg", "jpeg"],
            help="Clear, top-down views work best for accurate analysis."
        )

        image = None
        if uploaded_file:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Rooftop Image", use_column_width=True)
            except Exception as e:
                st.error(f"Failed to load image: {str(e)}")

    # Location and Settings
    with st.expander("⚙️ Analysis Parameters"):
        country = st.selectbox(
            "Country",
            list(GOVERNMENT_INCENTIVES.keys()),
            index=0
        )
        electricity_rate = st.number_input(
            "Local Electricity Rate (per kWh)",
            min_value=0.01,
            max_value=2.0,
            value=0.12,
            step=0.01
        )
        sun_hours = st.number_input(
            "Average Daily Sun Hours",
            min_value=1.0,
            max_value=12.0,
            value=4.5,
            step=0.1
        )

    # Solar Panel Information
    with st.expander("🔧 Solar Panel Types"):
        for panel_type, details in SOLAR_PANEL_TYPES.items():
            st.markdown(f"""
            <div class="panel-card">
                <h4>{panel_type}</h4>
                <p><strong>Efficiency:</strong> {details['efficiency']}</p>
                <p><strong>Cost:</strong> ₹{details['cost_per_watt']}/W</p>
                <p><strong>Lifespan:</strong> {details['lifespan']}</p>
                <p>{details['description']}</p>
            </div>
            """, unsafe_allow_html=True)

with col2:
    # Analysis Section
    if image and st.button("🔍 Analyze Rooftop", type="primary"):
        with st.spinner("Analyzing with AI (this may take 20-30 seconds)..."):
            try:
                analysis_result = analyze_rooftop_with_ai(image, country)
                
                st.subheader("📊 Professional Solar Assessment")
                st.markdown(analysis_result)
                
                # Save to session state
                st.session_state.analysis_result = analysis_result
                st.session_state.image = image
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

        # Extract system size for financial calculations
        if image and 'analysis_result' in st.session_state and "Recommended system size" in st.session_state['analysis_result']:
            analysis_result = st.session_state['analysis_result']
            try:
                system_size = float(analysis_result.split("Recommended system size")[1].split("kW")[0].strip())
                panel_type = analysis_result.split("Optimal panel type")[1].split("\n")[0].strip()
                financials = calculate_financials(
                    panel_type,
                    system_size,
                    electricity_rate,
                    sun_hours,
                    country
                )
                
                if financials:
                    st.subheader("💰 Financial Projections")
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>Financial Summary</h4>
                        <p><strong>Total System Cost:</strong> ₹{financials['total_cost']:,.2f}</p>
                        <p><strong>Annual Production:</strong> {financials['annual_production_kwh']:,.0f} kWh</p>
                        <p><strong>Annual Savings:</strong> ₹{financials['annual_savings']:,.2f}</p>
                        <p><strong>ROI Period:</strong> {financials['roi_years']:.1f} years</p>
                        <h5>Government Incentives:</h5>
                        <ul>
                            {"".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in financials['incentives'].items()])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Couldn't extract all financial details: {str(e)}")

# ROI Calculator
st.subheader("🧮 ROI Calculator")
with st.form("roi_form"):
    panel_watt = st.number_input("Panel Wattage (W)", min_value=100, max_value=700, value=400)
    panel_count = st.number_input("Number of Panels", min_value=1, max_value=100, value=10)
    cost_per_panel = st.number_input("Cost per Panel (₹)", min_value=5000, max_value=50000, value=22000, step=1000)
    electricity_rate = st.number_input("Electricity Rate (₹/kWh)", min_value=1.0, max_value=20.0, value=8.5, step=0.5)
    submitted = st.form_submit_button("Calculate ROI")
    if submitted:
        total_cost = panel_watt * panel_count * cost_per_panel / panel_watt
        annual_production = panel_watt * panel_count * 4.5 * 365 / 1000  # 4.5 sun hours, kWh/year
        savings = annual_production * electricity_rate
        roi = total_cost / savings if savings else float('inf')
        st.success(f"Total Installation Cost: ₹{total_cost}")
        st.success(f"Annual Savings: ₹{round(savings, 2)}")
        if roi == float('inf'):
            st.warning("Annual savings is zero, ROI cannot be calculated.")
        else:
            st.success(f"Estimated ROI: {roi} years")


                

    # Show saved analysis if available
    if 'analysis_result' in st.session_state:
        st.divider()
        st.subheader("Last Analysis")
        st.markdown(st.session_state['analysis_result'])
        
        # Download button
        st.download_button(
            label="📥 Download Full Report",
            data=st.session_state.analysis_result,
            file_name="solar_assessment_report.md",
            mime="text/markdown"
        )

# Footer
st.divider()
st.markdown("""
<div class="footer">
    <p>Solar Industry AI Assistant - Professional Tool for Solar Installers</p>
    <p>Note: Analysis results are estimates. Always consult with a certified solar installer.</p>
</div>
""", unsafe_allow_html=True)