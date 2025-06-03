import streamlit as st    # type: ignore
from PIL import Image # type: ignore
import io
import base64
import openai  # type: ignore # Ensure openai package is installed

# === Configuration ===
API_KEY = "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"  
# Replace with your actual key or load from environment variable

client = openai.OpenAI(api_key=API_KEY)

# === ROI Calculation ===
def calculate_roi(panel_watt, panel_count, cost_per_panel, electricity_rate, sun_hours_per_day=4.5):
    total_watt = panel_watt * panel_count
    annual_output_kwh = total_watt * sun_hours_per_day * 365 / 1000
    annual_savings = annual_output_kwh * electricity_rate
    total_cost = panel_count * cost_per_panel
    roi_years = round(total_cost / annual_savings, 2) if annual_savings else float('inf')
    return total_cost, annual_savings, roi_years

# === Vision Analysis ===
def analyze_image_with_gpt(image: Image.Image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    prompt = (
        "Analyze this rooftop image and provide:\n"
        "1. Usable rooftop area (in m²)\n"
        "2. Recommended number and type of solar panels (with wattage)\n"
        "3. Estimated installation cost and ROI (in years)\n"
        "4. Notes on shading or obstacles"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
            ]}
        ],
        max_tokens=800,
    )
    return response.choices[0].message.content

# === Streamlit UI ===
st.set_page_config(page_title="Solar Rooftop AI Tool", layout="centered")
st.title("☀️ Solar Rooftop Analysis AI Tool")

# Upload image
st.markdown("Upload a rooftop image or use the sample to analyze solar potential.")
uploaded_file = st.file_uploader("Upload Rooftop Image", type=["png", "jpg", "jpeg"])
default_path = "sample_rooftop.png"  # Optional: Add a default image in repo

if uploaded_file:
    image = Image.open(uploaded_file)
else:
    try:
        image = Image.open(default_path)
        st.info("Using sample image.")
    except:
        st.warning("Upload an image to continue.")
        image = None

if image:
    st.image(image, caption="Rooftop Image", use_container_width=True)

    if st.button("🔍 Analyze Rooftop"):
        with st.spinner("Analyzing with GPT-4o Vision..."):
            
            try:
                result = analyze_image_with_gpt(image)
                st.subheader("📊 AI Analysis Result")
                st.markdown(result)
            except openai.RateLimitError:
                st.error("Rate limit exceeded. Please try again later.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

# ROI Calculator
st.subheader("🧮 ROI Calculator")
with st.form("roi_form"):
    panel_watt = st.number_input("Panel Wattage (W)", value=540)
    panel_count = st.number_input("Number of Panels", value=10)
    cost_per_panel = st.number_input("Cost per Panel (₹)", value=22000)
    electricity_rate = st.number_input("Electricity Rate (₹/kWh)", value=8.5)
    submitted = st.form_submit_button("Calculate ROI")

    if submitted:
        total_cost, savings, roi = calculate_roi(panel_watt, panel_count, cost_per_panel, electricity_rate)
        st.success(f"Total Installation Cost: ₹{total_cost}")
        st.success(f"Annual Savings: ₹{round(savings, 2)}")
        if roi == float('inf'):
            st.warning("Annual savings is zero, ROI cannot be calculated.")
        else:
            st.success(f"Estimated ROI: {roi} years")



