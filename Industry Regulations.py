class SolarInstallation:
    def __init__(self, location, system_size_kw, has_bi_directional_meter, inverter_certified, meets_fire_code):
        self.location = location
        self.system_size_kw = system_size_kw
        self.has_bi_directional_meter = has_bi_directional_meter
        self.inverter_certified = inverter_certified
        self.meets_fire_code = meets_fire_code

    def check_building_code_compliance(self):
        # Example rule: Max 10kW in residential zones
        if self.system_size_kw > 10:
            return False, "Exceeds residential size limit"
        return True, "Compliant with building code"

    def check_net_metering_eligibility(self):
        # Net metering requires bi-directional meter
        if not self.has_bi_directional_meter:
            return False, "Missing bi-directional meter"
        return True, "Eligible for net metering"

    def check_safety_standards(self):
        # Must have certified inverter and meet fire code
        if not self.inverter_certified:
            return False, "Inverter not certified"
        if not self.meets_fire_code:
            return False, "Fails fire safety compliance"
        return True, "Meets safety standards"

    def run_all_checks(self):
        results = {
            "Building Code": self.check_building_code_compliance(),
            "Net Metering": self.check_net_metering_eligibility(),
            "Safety Standards": self.check_safety_standards()
        }
        return results


# Example usage:
installation = SolarInstallation(
    location="California",
    system_size_kw=8,
    has_bi_directional_meter=True,
    inverter_certified=True,
    meets_fire_code=True
)

checks = installation.run_all_checks()

# # Output results
# for category, (status, message) in checks.items():
#     print(f"{category}: {'✅ Passed' if status else '❌ Failed'} - {message}")
