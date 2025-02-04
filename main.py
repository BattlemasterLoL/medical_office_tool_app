from nicegui import ui, app, Client
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from ollama import AsyncClient
import os
import io
import PyPDF2
from PyPDF2.generic import NameObject
from datetime import datetime

# Functions ======================================================================================
#%% ========== ICD Lookup Functions ==============================================================
class ICDLookup:
    def __init__(self):
        self.lookup_term = None
        self.lookup_lab = None
        self.ICDresults = None
        self.ICDcontainer = None

    def icd_lookup(self):
        if self.lookup_lab is None or self.ICDresults is None or self.ICDcontainer is None:
            print("UI components are not initialized. Please call ICD_UI_SetUp first.")
            return

        url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code,name&terms="

        # Get results
        response = requests.get(url + self.lookup_term.value)
        data = json.loads(response.content)
        nresults = data[0]
        icd_codes = data[1]
        # Already a list of pairs, no need to convert
        icd_pairs = dict(data[3])

        # Clear all
        self.lookup_lab.clear()
        self.ICDresults.clear()
        self.ICDcontainer.remove(0)

        self.lookup_lab.set_text(f"{self.lookup_term.value} returned {nresults} results")
        self.lookup_lab.style("font-size: 14px")

        # Add results to table
        df = pd.DataFrame(icd_pairs.items())

        with self.ICDcontainer.classes("w-full items-center").style("align-items: center;"):
            self.ICDresults = ui.aggrid.from_pandas(df).style("width:60%; min-height: 500px")
        
        self.ICDresults.options["columnDefs"][0]["width"] = "50px"
        self.ICDresults.options["columnDefs"][0]["headerName"] = "Code"
        self.ICDresults.options["columnDefs"][1]["headerName"] = "Description"

    def ICD_reset(self):
        if self.ICDcontainer is None:
            print("ICD container is not initialized. Please call ICD_UI_SetUp first.")
            return

        self.ICDcontainer.remove(0)
        with self.ICDcontainer.classes("w-full items-center").style("align-items: center;"):
            self.ICDresults = ui.aggrid({}).style("width:60%; min-height: 500px; padding-top: 20px")

    def ICD_UI_SetUp(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label("ICD10 Lookup").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')

            self.lookup_term = ui.input("Enter Code or Term to lookup").style("width: 60%")
            with ui.row():
                ui.button("Search", on_click=self.icd_lookup).style("width:150px")
                ui.button("Reset", on_click=self.ICD_reset).style("width:150px")

            self.ICDcontainer = ui.column()
            with self.ICDcontainer.classes("w-full items-center").style("align-items: center;"):
                self.ICDresults = ui.aggrid({}).style("width:60%; min-height: 500px; padding-top: 20px")

            self.lookup_lab = ui.label("").style("font-size: 14px;")  # Initialize lookup_lab here

            ui.html('ICD10 codes based on <a href="https://clinicaltables.nlm.nih.gov/" target="_blank" style="color: #6FA5D8;">NIH database</a>')


#%% ========== Insulin & Glucose Plot ============================================================
class InsulinGlucosePlot:
    def __init__(self):
        self.i1 = None
        self.i2 = None
        self.i3 = None
        self.i4 = None
        self.g1 = None
        self.g2 = None
        self.g3 = None
        self.g4 = None
        self.insulin_chart = None
        self.glucose_chart = None

    def gather_data_ins_glu(self):
        if self.i1 is None or self.i2 is None or self.i3 is None or self.i4 is None:
            print("Input fields are not initialized. Please call InsGlu_UI_Setup first.")
            return

        insulin = [self.i1.value, self.i2.value, self.i3.value, self.i4.value]
        glucose = [self.g1.value, self.g2.value, self.g3.value, self.g4.value]
        
        for i, (ins, glu) in enumerate(zip(insulin, glucose)):
            self.insulin_chart.options["series"][5]["data"][i][1] = float(ins)
            self.glucose_chart.options["series"][3]["data"][i][1] = float(glu)
        
        self.insulin_chart.update()
        self.glucose_chart.update()

    def save_chart_ins_glu(self):    
        # Implement saving functionality here
        pass

    def InsGlu_UI_Setup(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label(text="Insulin and Glucose Pattern Identifier").style(
                "font-weight: bold; font-size: 25px;"
            )
            ui.separator().style('width: 85%')
            ui.label(text="Patient Lab Results").style(
                "font-size: 16px; padding-top: 10px;"
            )
            with ui.row():
                self.i1 = ui.input("Baseline Insulin").style("width: 300px")
                self.g1 = ui.input("Baseline Glucose").style("width: 300px")
            with ui.row():
                self.i2 = ui.input("30 Minute Insulin").style("width: 300px")
                self.g2 = ui.input("30 Minute Glucose").style("width: 300px")
            with ui.row():
                self.i3 = ui.input("60 Minute Insulin").style("width: 300px")
                self.g3 = ui.input("60 Minute Glucose").style("width: 300px")
            with ui.row():
                self.i4 = ui.input("120 Minute Insulin").style("width: 300px")
                self.g4 = ui.input("120 Minute Glucose").style("width: 300px")
            with ui.row():
                ui.button(text="Generate Plot", on_click=self.gather_data_ins_glu).style("width:150px")
                ui.button(text="Save Figure", on_click=self.save_chart_ins_glu).style("width:150px")

            self.insulin_chart = (
                ui.highchart(
                    {
                        "title": {"text": "Insulin Response"},
                        "xAxis": {"title": {"text": "Time (min)"}},
                        "yAxis": {"title": {"text": "Insulin Level (uIU/ml)"}},
                        "chart": {"type": "line", "borderRadius": "10"},
                        "series": [
                            {
                                "name": "Pattern 1",
                                "data": [[0, 8], [30, 59], [60, 61], [120, 30]],
                                "color": "#9FE9EF",
                            },
                            {
                                "name": "Pattern 2",
                                "data": [[0, 13], [30, 93], [60, 116], [120, 80]],
                                "color": "#62D1E4",
                            },
                            {
                                "name": "Pattern 3",
                                "data": [[0, 13], [30, 64], [60, 93], [120, 133]],
                                "color": "#25B0DA",
                            },
                            {
                                "name": "Pattern 4",
                                "data": [[0, 56], [30, 147], [60, 165], [120, 185]],
                                "color": "#1B749D",
                            },
                            {
                                "name": "Pattern 5",
                                "data": [[0, 5], [30, 15], [60, 16], [120, 15]],
                                "color": "#104060",
                            },
                            {
                                "name": "Patient",
                                "data": [[0, 0], [30, 0], [60, 0], [120, 0]],
                                "lineWidth": 4,
                                "color": "#061523",
                            },
                        ],
                    }
                )
                .classes("w-500 h-300")
                .style("padding-top: 15px;")
            )

            self.glucose_chart = (
                ui.highchart(
                    {
                        "title": {"text": "Glucose Response"},
                        "xAxis": {"title": {"text": "Time (min)"}},
                        "yAxis": {"title": {"text": "Glucose Level (mg/dL)"}},
                        "chart": {"type": "line", "borderRadius": "10"},
                        "series": [
                            {
                                "name": "Normal",
                                "data": [[0, 80], [30, 130], [60, 120], [120, 100]],
                                "color": "green",
                            },
                            {
                                "name": "Impaired Glucose Tolerance",
                                "data": [[0, 95], [30, 180], [60, 170], [120, 140]],
                                "color": "orange",
                            },
                            {
                                "name": "Diabetes",
                                "data": [[0, 110], [30, 220], [60, 210], [120, 180]],
                                "color": "red",
                            },
                            {
                                "name": "Patient",
                                "data": [[0, 0], [30, 0], [60, 0], [120, 0]],
                                "lineWidth": 4,
                                "color": "#061523",
                                "marker": {
                                    "symbol": "circle",
                                    "radius": 6,
                                }
                            },
                        ],
                    }
                )
                .classes("w-500 h-300")
                .style("padding-top: 15px;")
            )

            ui.markdown(
                """
                        |  Pattern  | <div style='width: 30em'>Description</div> |
                        | --------- | ----------- |
                        | Pattern 1 | Info Here |
                        | Pattern 2 | Info Here |
                        | Pattern 3 | Info Here |
                        | Pattern 4 | Info Here |
                        | Pattern 5 | Info Here |
                        """
            )
            ui.html(
                """
                    Pattern data based on Dr. Kraft's method. (
                    <a href="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5708305/" target="_blank" style="color: #6FA5D8;">Paper</a>, 
                    <a href="https://www.amazon.com/Diabetes-Epidemic-Joseph-Kraft-FCAP-ebook/dp/B0791MLR8W/ref=sr_1_1?crid=36RLSBXU6UUDR&dib=eyJ2IjoiMSJ9.LtcQ9Oyfy_gB6JVhrlS9MTOWF8ygRCXjMAQ0k1DOxjkb5IhsAVZhteg76AvUGjDE1BzvrBjm3psfl6C2vNCTFsvMr35b9knk6MKQd2PDa5wfJ74qpuMqELfFXuPYpAOjuAUoNQFwZM2YMhKlOnUGS7nxg0aR6qgNKyxI6kT4Hmp9twZPndCubWRPeqSotmho8DU01qhJbQCakJ-ojLipelXHIZ7wowzkJ5y4IrYKmgU.LrvywcvIOx19BQQ4crlv_sdmqWQT9IH9oxo5CGhiXG0&dib_tag=se&keywords=Diabetes+Epidemic+%26+You&qid=1708445142&sprefix=diabetes+epidemic+%26+you%2Caps%2C320&sr=8-1" target="_blank" style="color: #6FA5D8;">Book</a>
                    )
                    """
            )

#%% ========== Wound Tracker Plot ================================================================
class WoundTracker:
    def __init__(self):
        self.dates = None
        self.w_width = None
        self.w_length = None
        self.w_depth = None
        self.unit_select = None
        self.plot = None
        self.fig = None

    def generate_plot(self):
        if self.dates is None or self.w_width is None or self.w_length is None or self.w_depth is None:
            print("UI components are not initialized. Please call woundtracker_UI_Setup first.")
            return

        # Split data
        sp_dates = self.dates.value.split("\n")
        sp_width = self.w_width.value.split("\n")
        sp_length = self.w_length.value.split("\n")
        sp_depth = self.w_depth.value.split("\n")

        # Validate and convert to float
        try:
            sp_width = [float(x) for x in sp_width]
            sp_length = [float(x) for x in sp_length]
            sp_depth = [float(x) for x in sp_depth]
        except ValueError:
            print("Please enter valid numeric values.")
            return

        sp_vol = [
            width * length * depth
            for width, length, depth in zip(sp_width, sp_length, sp_depth)
        ]

        # Plot using Plotly
        self.fig.add_trace(
            go.Scatter(
                x=sp_dates, y=sp_width, mode="lines+markers", name="Wound Width", yaxis="y1"
            )
        )
        self.fig.add_trace(
            go.Scatter(
                x=sp_dates,
                y=sp_length,
                mode="lines+markers",
                name="Wound Length",
                yaxis="y1",
            )
        )
        self.fig.add_trace(
            go.Scatter(
                x=sp_dates, y=sp_depth, mode="lines+markers", name="Wound Depth", yaxis="y1"
            )
        )
        self.fig.add_trace(
            go.Scatter(
                x=sp_dates, y=sp_vol, mode="lines+markers", name="Wound Volume", yaxis="y2"
            )
        )
        self.fig.update_layout(
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Size ({})".format(self.unit_select.value)),
            yaxis2=dict(
                title="Volume ({})^2".format(self.unit_select.value),
                overlaying="y",
                side="right",
                tickmode="sync",
                autoshift=True,
            ),
        )
        ui.update(self.plot)

    def reset_plot(self):
        if self.dates is None or self.w_width is None or self.w_length is None or self.w_depth is None:
            print("UI components are not initialized. Please call woundtracker_UI_Setup first.")
            return

        self.dates.set_value("")
        self.w_width.set_value("")
        self.w_length.set_value("")
        self.w_depth.set_value("")
        self.fig.data = []
        ui.update(self.plot)

    def woundtracker_UI_Setup(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label(text="Wound Dimensions Tracker").style(
                "font-weight: bold; font-size: 25px;"
            )
            ui.separator().style('width: 85%')
            with ui.row():
                self.dates = ui.textarea("Measurement Dates").style("width: 300px")
                self.w_width = ui.textarea("Wound Width").style("width: 300px")
            with ui.row():
                self.w_length = ui.textarea("Wound Length").style("width: 300px")
                self.w_depth = ui.textarea("Wound Depth").style("width: 300px")
            with ui.row():
                self.unit_select = ui.select(["cm", "mm", "in"], value="cm").style("width: 50px;")
                ui.button(text="Generate Plot", on_click=self.generate_plot).style(
                    "margin-top: 20px; width:150px"
                )
                ui.button(text="Reset Plot", on_click=self.reset_plot).style(
                    "margin-top: 20px; width:150px"
                )
            with ui.row().style("padding: 10px"):
                self.fig = go.Figure()
                self.fig.update_layout(
                    title=" Wound Dimensions",
                    margin=dict(l=0, r=0, t=30, b=0),
                )

                self.plot = ui.plotly(self.fig).classes("w-full h-82")


#%% ========== Cost Extimator ====================================================================
class CostEstimator:
    def __init__(self):
        self.fee_df = pd.read_csv("fee_schedule.csv")
        self.ins_list = self.fee_df.columns[4:].tolist()
        
        # Initialize UI components
        self.codes = None
        self.ins_choice = None
        self.codes_ordered = None
        self.INScontainer = None
        self.ideductible = None
        self.imet_deductible_amount = None
        self.iout_of_pocket = None
        self.imet_out_of_pocket_amount = None
        self.iinsurance_percent = None
        self.ipatient_payment = None
        self.iinsurance_payment = None
        self.est_cost = 0
        self.Cresults = None

    def get_cost(self):
        if self.ins_choice is None or not self.ins_choice.value:
            ui.notify("Please select an insurance option first.", position="center", type="negative")
            return

        s_code = self.codes.value.split("\n")
        unknown_codes = [code for code in s_code if code not in self.fee_df["CPT"].values]

        if unknown_codes:
            ui.notify(
                f"The following CPT codes are not in the list: {', '.join(unknown_codes)}",
                position="center",
                type="negative",
            )
            return

        self.INScontainer.remove(0)
        pt_ins = self.ins_choice.value

        # Initialize the lists for the dataframe
        s_code_list = []
        desc_list = []
        cost_list = []
        rvu_list = []

        for code in s_code:
            try:
                # Get the data for the current code
                code_df = self.fee_df.loc[self.fee_df["CPT"] == code]
                if code_df.empty:
                    raise ValueError(f"No data found for CPT code: {code}")

                cost = code_df[pt_ins].astype(float).values[0]
                rvu = code_df["Total RVU Office"].astype(float).values[0]
                desc = code_df["Description"].values[0]

                # Add the data to the respective lists
                s_code_list.append(code)
                desc_list.append(desc)
                cost_list.append(cost)
                rvu_list.append(rvu)
            except Exception as e:
                ui.notify(f"Error processing code {code}: {str(e)}", position="center", type="negative")
                return

        # Create the dataframe
        cost_df = pd.DataFrame(
            data={
                "Codes": s_code_list,
                "Description": desc_list,
                "Cost": cost_list,
                "RVU": rvu_list,
            }
        )
        # Reset the index of the cost_df dataframe
        cost_df = cost_df.reset_index(drop=True)

        # Convert the 'RVU' column to numeric values
        cost_df["RVU"] = pd.to_numeric(cost_df["RVU"], errors='coerce')

        # Find the maximum RVU
        max_rvu = cost_df["RVU"].max()

        # Create a new column 'Adjusted Cost'
        cost_df["Adj Cost"] = cost_df.apply(
            lambda row: row["Cost"] * 0.5 if row["RVU"] == max_rvu else row["Cost"], axis=1
        )

        with self.INScontainer.classes("w-full items-center").style("align-items: center;"):
            self.Cresults = ui.aggrid.from_pandas(cost_df).style("width:80%; min-height: 500px")
        
        self.Cresults.options["columnDefs"][0]["width"] = "50px"
        self.Cresults.options["columnDefs"][2]["width"] = "50px"
        self.Cresults.options["columnDefs"][3]["width"] = "50px"
        self.Cresults.options["columnDefs"][4]["width"] = "50px"

        # Get estimated cost
        self.est_cost = sum(cost_df["Adj Cost"])
        # Sort the dataframe by 'RVU' in descending order
        cost_df = cost_df.sort_values(by="RVU", ascending=False)
        # Get the code of the top RVU
        top_code = cost_df["Codes"].tolist()

        # Order codes and add results
        ordered_out = []
        for code in top_code:
            ordered_out.append(code)
        ordered_out.append(f"Cost: ${self.est_cost:.2f}")
        self.codes_ordered.value = "\n".join(ordered_out)

        pt_out, ins_out = self.calculate_payment()
        self.ipatient_payment .value = pt_out
        self.iinsurance_payment.value = ins_out

        ui.notify("Cost estimation completed successfully.", position="center", type="positive")

    def cost_reset(self):
        self.INScontainer.remove(0)
        self.codes_ordered.value = ""
        self.codes.value = ""
        self.ins_choice.value = ""
        self.ideductible.value = ""
        self.imet_deductible_amount.value = ""
        self.iout_of_pocket.value = ""
        self.imet_out_of_pocket_amount.value = ""
        self.iinsurance_percent.value = ""
        self.ipatient_payment.value = ""
        self.iinsurance_payment.value = ""
        with self.INScontainer.classes("w-full items-center").style("align-items: center;"):
            self.Cresults = ui.aggrid({}).style("width:80%; min-height: 500px")

    def calculate_payment(self):
        if self.ins_choice.value == "Self Pay" or self.ideductible.value == "":
            pt_out = f"${self.est_cost:.2f}"
            ins_out = "N/A"
            return pt_out, ins_out

        # Get from entry
        cost_before_insurance = float(self.est_cost)
        deductible = float(self.ideductible.value)
        met_deductible_amount = float(self.imet_deductible_amount.value)
        out_of_pocket = float(self.iout_of_pocket.value)
        met_out_of_pocket_amount = float(self.imet_out_of_pocket_amount.value)
        insurance_percent = float(self.iinsurance_percent.value)

        # Initialize
        patient_payment = 0
        insurance_payment = 0

        # Step 1: Patient is fully responsible up to the deductible amount
        if met_deductible_amount < deductible:
            remaining_deductible_amount = deductible - met_deductible_amount
            if cost_before_insurance <= remaining_deductible_amount:
                patient_payment += round(cost_before_insurance, 2)
                met_deductible_amount += round(cost_before_insurance, 2)
            else:
                patient_payment += round(remaining_deductible_amount, 2)
                met_deductible_amount = deductible

        # Step 2: Insurance covers a percentage until out-of-pocket maximum is met
        if met_deductible_amount >= deductible and met_out_of_pocket_amount < out_of_pocket:
            remaining_cost = cost_before_insurance - patient_payment
            patient_percent_payment = round(
                min(remaining_cost, out_of_pocket - met_out_of_pocket_amount) * (1 - insurance_percent / 100),
                2,
            )
            patient_payment += patient_percent_payment
            insurance_payment += round(
                min(remaining_cost - patient_percent_payment, out_of_pocket - met_out_of_pocket_amount),
                2,
            )

            # Check if there's a remaining amount after step 2
            remaining_after_step_2 = cost_before_insurance - patient_payment - insurance_payment
            if remaining_after_step_2 > 0:
                # Proceed to Step 3
                insurance_payment += round(remaining_after_step_2, 2)

        # Step 3: Insurance covers the full remaining cost after out-of-pocket maximum is met
        if met_out_of_pocket_amount >= out_of_pocket:
            insurance_payment += round(cost_before_insurance - patient_payment, 2)

        # Output
        pt_out = f"${patient_payment:.2f}"
        ins_out = f"${insurance_payment:.2f}"
        return pt_out, ins_out

    def cost_estimator_UI_Setup(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label("Treatment Cost Estimator").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')
            with ui.row():
                self.ins_choice = ui.select(self.ins_list, with_input=True, label="Insurance").style("width: 40em")
            with ui.grid(columns=2).style("align-items: center;"):
                self.codes = ui.textarea("Codes").style("width: 275px").props("clearable")
                self.codes_ordered = ui.textarea("Ordered Codes & Cost").style("width: 275px")

                self.ideductible = ui.input("Deductible")
                self.imet_deductible_amount = ui.input("Met Deductible")

                self.iout_of_pocket = ui.input("Out-of-Pocket")
                self.imet_out_of_pocket_amount = ui.input("Met Out-of-Pocket")

                self.iinsurance_percent = ui.input("Co-Insurance %")
                ui.label("")

                self.ipatient_payment = ui.input("Patient Payment")
                self.iinsurance_payment = ui.input("Insurance Payment")

            with ui.row():
                ui.button("Calculate Cost", on_click=self.get_cost).style("width:150px")
                ui.button("Reset", on_click=self.cost_reset).style("width:150px")

            self.INScontainer = ui.column().style("padding: 10px")
            with self.INScontainer.classes("w-full items-center").style("align-items: center;"):
                self.Cresults = ui.aggrid({}).style("width:80%; min-height: 500px")


#%% ========== NPI Lookup ========================================================================
class NPILookup:
    def __init__(self):
        # Initialize UI components
        self.NPIcontainer = None
        self.first_name = None
        self.last_name = None
        self.state = None
        self.NPInumber = None
        self.NPIresults = None

        # Set up the UI
        self.setup_ui()

    def setup_ui(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label("NPI Lookup").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')
            with ui.grid(columns=2).style("align-items: center; width: 40em"):
                self.first_name = ui.input("First Name")
                self.last_name = ui.input("Last Name")
                self.state = ui.input("State (ex UT)", validation={"Too long": lambda value: len(value) <= 2})
                self.NPInumber = ui.input("NPI Number")

                ui.button("Get Results", on_click=self.lookup_npi).style("width:150px")
                ui.button("Reset", on_click=self.NPI_reset).style("width:150px")

            self.NPIcontainer = ui.column().style("padding: 10px")
            with self.NPIcontainer.classes('w-full items-center').style('align-items: center;'):
                self.NPIresults = ui.aggrid({}).style('width:80%; min-height: 500px')

    def lookup_npi(self):
        self.NPIcontainer.remove(0)

        url = f'https://npiregistry.cms.hhs.gov/api/?number={self.NPInumber.value}&first_name={self.first_name.value}&last_name={self.last_name.value}&state={self.state.value}&pretty=on&version=2.1'
        response = requests.get(url)
        NPIdata = json.loads(response.content)

        def access_field(results, field, sub_field):
            values = []
            for item in results:
                if field in item:
                    basic_info = item[field]
                    if sub_field in basic_info:
                        value = basic_info[sub_field]
                        values.append(value)
                    else:
                        values.append('n/a')
                else:
                    values.append('n/a')
            return values

        def access_field_list(results, field, sub_field):
            values = []
            for item in results:
                if field in item:
                    basic_info = item[field][0]
                    if sub_field in basic_info:
                        value = basic_info[sub_field]
                        values.append(value)
                    else:
                        values.append('None')
                else:
                    values.append('None')
            return values

        numbers = [result['number'] for result in NPIdata['results']]
        first_names = access_field(NPIdata['results'], 'basic', 'first_name')
        last_names = access_field(NPIdata['results'], 'basic', 'last_name')
        middle_names = access_field(NPIdata['results'], 'basic', 'middle_name')
        credentials = access_field(NPIdata['results'], 'basic', 'credential')
        genders = access_field(NPIdata['results'], 'basic', 'gender')
        states = access_field_list(NPIdata['results'], 'taxonomies', 'state')
        taxonomies = access_field_list(NPIdata['results'], 'taxonomies', 'code')
        descs = access_field_list(NPIdata['results'], 'taxonomies', 'desc')

        df = pd.DataFrame(data={
            'NPI Number': numbers,
            'First Name': first_names,
            'Last Name': last_names,
            'Middle Name': middle_names,
            'Credential': credentials,
            'Sex': genders,
            'State': states,
            'Taxonomy Code': taxonomies,
            'Description': descs
        })

        record_data = df.to_dict('records')
        with self.NPIcontainer.classes('w-full items-center').style('align-items: center;'):
            self.NPIresults = ui.aggrid({
                'columnDefs': [
                    {'headerName': 'NPI Number', 'field': 'NPI Number', 'width': '120px', 'singleClickEdit': True, ':editable': True},
                    {'headerName': 'First Name', 'field': 'First Name', 'width': '120px'},
                    {'headerName': 'Last Name', 'field': 'Last Name', ' width': '120px'},
                    {'headerName': 'Middle Name', 'field': 'Middle Name', 'width': '110px'},
                    {'headerName': 'Credential', 'field': 'Credential', 'width': '100px'},
                    {'headerName': 'Sex', 'field': 'Sex', 'width': '50px'},
                    {'headerName': 'State', 'field': 'State', 'width': '70px', 'filter': 'agTextColumnFilter', 'floatingFilter': True},
                    {'headerName': 'Taxonomy Code', 'field': 'Taxonomy Code', 'width': '130px', 'singleClickEdit': True, ':editable': True},
                    {'headerName': 'Description', 'field': 'Description', 'flex': 1, 'filter': 'agTextColumnFilter', 'floatingFilter': True}
                ],
                'rowData': record_data
            }).style('width:80%; min-height: 500px')

    def NPI_reset(self):
        self.NPIcontainer.remove(0)
        self.first_name.value = ''
        self.last_name.value = ''
        self.state.value = ''
        self.NPInumber.value = ''
        with self.NPIcontainer.classes('w-full items-center').style('align-items: center;'):
            self.NPIresults = ui.aggrid({}).style('width:60%; min-height: 500px; padding-top: 20px')


#%% ========== Dr/Rep Info Lookup ================================================================
class InfoLookup:
    def __init__(self):
        # Load dataframes
        self.DR_df = pd.read_csv("doctor_info.csv")
        self.REP_df = pd.read_csv("rep_info.csv")

        # Initialize UI components
        self.REP_select = None
        self.repname_lab = None
        self.repcomp_lab = None
        self.repphone_lab = None
        self.repfax_lab = None
        self.drfirst_name = None
        self.drlast_name = None
        self.drname_lab = None
        self.drspec_lab = None
        self.drnpi_lab = None
        self.drloc1_lab = None
        self.drphone_lab = None
        self.drfax_lab = None
        self.info_cat_select = None
        self.add_first = None
        self.add_last = None
        self.add_specialty = None
        self.add_npi = None
        self.add_phone = None
        self.add_fax = None
        self.add_street = None
        self.add_city = None
        self.add_state = None
        self.add_zip = None

        # Set up the UI
        self.setup_ui()

    def setup_ui(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label(text="Info Lookup").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')
            lookup_toggle = ui.toggle({1: "Company Rep", 2: "Physician", 3: "Add Info"}, value=1)

            # Container setup
            rep_container = ui.column().bind_visibility_from(lookup_toggle, "value", value=1)
            dr_container = ui.column().bind_visibility_from(lookup_toggle, "value", value=2)
            addinfo_container = ui.column().bind_visibility_from(lookup_toggle, "value", value=3)

            # Company Rep Container
            with rep_container.classes("w-full items-center").style("align-items: center;"):
                self.REP_select = ui.select(list(self.REP_df["Company"]), label="Company", with_input=True, on_change=self.get_rep_info).style("width: 30em")

                with ui.grid(columns=2).style("align-items: center; width: 25em; grid-template-columns: 15px auto; grid-template-rows: 2.5em 2.5em"):
                    ui.icon("person").classes("text-3xl")
                    self.repname_lab = ui.label("Waiting...")

                    ui.icon("store").classes("text-3xl")
                    self.repcomp_lab = ui.label("Waiting...")

                    ui.icon("phone").classes("text-3xl")
                    self.repphone_lab = ui.label("Waiting...")

                    ui.icon("email").classes("text-3xl")
                    self.repfax_lab = ui.label("Waiting...")

                ui.button("Reset", on_click=self.rep_reset).style("width: 150px; padding-top: 25px")

            # Physician Container
            with dr_container.classes("w-full items-center").style("align-items: center;"):
                with ui.grid(columns=2).style("align-items: center; width: 40em"):
                    self.drfirst_name = ui.input("First Name", autocomplete=list(self.DR_df["First"]))
                    self.drlast_name = ui.input("Last Name", autocomplete=list(self.DR_df["Last"]))

                with ui.grid(columns=2).style("align-items: center; width: 25em; grid-template-columns: 15px auto; grid-template-rows: 2.5em 2.5em 2.5em 2.5em 2.5em 2.5em").classes("mx-auto gap-x-24"):
                    ui.icon("person").classes("text-3xl")
                    self.drname_lab = ui.label("Waiting...")

                    ui.icon("local_hospital").classes("text-3xl")
                    self.drspec_lab = ui.label("Waiting...")

                    ui.icon("badge").classes("text-3xl")
                    self.drnpi_lab = ui.label("Waiting...")

                    ui.icon("location_on").classes("text-3xl")
                    self.drloc1_lab = ui.label("Waiting...")

                    ui.icon("phone").classes("text-3xl")
                    self.drphone_lab = ui.label("Waiting...")

                    ui.icon ("fax").classes("text-3xl")
                    self.drfax_lab = ui.label("Waiting...")

                with ui.grid(columns=2).style("align-items: center; width: 40em"):
                    ui.button("Get Info", on_click=self.get_dr_info).style("width:150px")
                    ui.button("Reset", on_click=self.dr_reset).style("width:150px")

            # Add Info Container
            with addinfo_container.classes("w-full items-center").style("align-items: center;"):
                self.info_cat_select = ui.select(["Rep", "Doctor"], label="Category").style("width: 30em")
                with ui.grid(columns=2).style("align-items: center; width: 40em"):
                    self.add_first = ui.input(label="First")
                    self.add_last = ui.input(label="Last")

                    self.add_specialty = ui.input(label="Specialty/Company")
                    self.add_npi = ui.input(label="NPI (Doctor Only)")

                    self.add_phone = ui.input(label='Phone')
                    self.add_fax = ui.input(label='Fax/E-Mail')

                    self.add_street = ui.input(label='Street (Doctor Only)')
                    self.add_city = ui.input(label='City (Doctor Only)')

                    self.add_state = ui.input(label='State (Doctor Only)')
                    self.add_zip = ui.input(label='Zip (Doctor Only)')

                with ui.grid(columns=2).style("align-items: center; width: 40em"):
                    ui.button("Add Info", on_click=self.add_info).style("width:150px")
                    ui.button("Reset", on_click=self.add_reset).style("width:150px")

    def get_rep_info(self):
        rep_company = self.REP_select.value
        mask = self.REP_df["Company"].str.strip() == rep_company
        result = self.REP_df.loc[mask]
        if not result.empty:
            row = result.iloc[0]
            self.repname_lab.text = f"{row['First']} {row['Last']}"
            self.repcomp_lab.text = f"{row['Company']}"
            self.repphone_lab.text = f"{row['Phone']}"
            self.repfax_lab.text = f"{row['Email']}"
        else:
            self.repname_lab.text = "Not Found"
            self.repcomp_lab.text = "Not Found"
            self.repphone_lab.text = "Not Found"
            self.repfax_lab.text = "Not Found"

    def rep_reset(self):
        self.REP_select.value = ""
        self.repname_lab.text = "Waiting..."
        self.repcomp_lab.text = "Waiting..."
        self.repphone_lab.text = "Waiting..."
        self.repfax_lab.text = "Waiting..."

    def get_dr_info(self):
        first_name_capitalized = self.drfirst_name.value.capitalize()
        last_name_capitalized = self.drlast_name.value.capitalize()

        mask = (self.DR_df["First"].str.strip() == first_name_capitalized) & (self.DR_df["Last"].str.strip() == last_name_capitalized)
        result = self.DR_df.loc[mask]
        if not result.empty:
            row = result.iloc[0]
            self.drname_lab.text = f"{row['First']} {row['Last']}"
            self.drspec_lab.text = f"{row['Specialty']}"
            self.drnpi_lab.text = f"{row['NPI']}"
            self.drloc1_lab.text = f"{row['Street']}\n{row['City']}, {row['State']} {row['Zip']}"
            self.drphone_lab.text = f"{row['Phone']}"
            self.drfax_lab.text = f"{row['Fax']}"
        else:
            self.drname_lab.text = "Not Found"
            self.drspec_lab.text = "Not Found"
            self.drnpi_lab.text = "Not Found"
            self.drloc1_lab.text = "Not Found"
            self.drphone_lab.text = "Not Found"
            self.drfax_lab.text = "Not Found"

    def dr_reset(self):
        self.drfirst_name.value = ""
        self.drlast_name.value = ""
        self.drname_lab.text = "Waiting..."
        self.drspec_lab.text = "Waiting..."
        self.drnpi_lab.text = "Waiting..."
        self.drloc1_lab.text = "Waiting..."
        self.drphone_lab.text = "Waiting..."
        self.drfax_lab.text = "Waiting..."

    def add_info(self):
        category = self.info_cat_select.value
        first = self.add_first.value
        last = self.add_last.value

        if category == "Rep":
            company = self.add_specialty.value
            phone = self.add_phone.value
            email = self.add_fax.value

            # Check if company already exists
            mask = (self.REP_df['Company'].str.strip() == company)
            if mask.any():
                # Update existing company
                self.REP_df.loc[mask, 'Phone'] = phone
                self.REP_df.loc[mask, 'Email'] = email
            else:
                # Add new company
                new_row = pd.DataFrame([[company, phone, email]], columns=['Company', 'Phone', 'Email'])
                self.REP_df = pd.concat([self.REP_df, new_row])

            self.REP_df.to_csv('rep_info.csv', index=False)

            self.add_first.value = ""
            self.add_last.value = ""
            self.add_specialty.value = ""
            self.add_phone.value = ""
            self.add_fax.value = ""

        elif category == "Doctor":
            specialty = self.add_specialty.value
            npi = self.add_npi.value
            phone = self.add_phone.value
            fax = self.add_fax.value
            street = self.add_street.value
            city = self.add_city.value
            state = self.add_state.value
            zip_code = self.add_zip.value

            # Check if doctor already exists
            mask = (self.DR_df['First'].str.strip() == first) & (self.DR_df['Last'].str.strip() == last)
            if mask.any():
                # Update existing doctor
                self.DR_df.loc[mask, 'Specialty'] = specialty
                self.DR_df.loc[mask, 'NPI'] = npi
                self.DR_df.loc[mask, 'Phone'] = phone
                self.DR_df.loc[mask, 'Fax'] = fax
                self.DR_df.loc[mask, 'Street'] = street
                self.DR_df.loc[mask, 'City'] = city
                self.DR_df.loc[mask, 'State'] = state
                self.DR_df.loc[mask, 'Zip'] = zip_code
            else:
                # Add new doctor
                new_row = pd.DataFrame([[first, last, specialty, npi, phone, fax, street, city, state, zip_code]], columns=self.DR_df.columns)
                self.DR_df = pd.concat([self.DR_df, new_row])

            self.DR_df.to_csv('doctor_info.csv', index=False)

            self.add_first.value = ""
            self.add_last.value = ""
            self.add_specialty.value = ""
            self.add_npi.value = ""
            self.add_phone.value = ""
            self.add_fax.value = ""
            self.add_street.value = ""
            self.add_city.value = ""
            self.add_state.value = ""
            self.add_zip.value = ""

    def add_reset(self):
        self.info_cat_select.value = ""
        self.add_first.value = ""
        self.add_last.value = ""
        self.add_specialty.value = ""
        self.add_npi.value = ""
        self.add_phone.value = ""
        self.add_fax.value = ""
        self.add_street.value = ""
        self.add_city.value = ""
        self.add_state.value = ""
        self.add_zip.value = ""


#%% ========== MME Calculator ====================================================================
class MMECalculator:
    def __init__(self):
        # Initialize instance variables
        self.mme_row = [
            {"drug": "Codeine", "dose": 0, "freq": 1, "cfactor": 0.15},
            {"drug": "Hydrocodone", "dose": 0, "freq": 1, "cfactor": 1},
            {"drug": "Hydromorphone", "dose": 0, "freq": 1, "cfactor": 4},
            {"drug": "Morphine", "dose": 0, "freq": 1, "cfactor": 1},
            {"drug": "Oxycodone", "dose": 0, "freq": 1, "cfactor": 1.5},
            {"drug": "Oxymorphone", "dose": 0, "freq": 1, "cfactor": 3},
            {"drug": "Tramadol", "dose": 0, "freq": 1, "cfactor": 0.1},
        ]
        self.mme_total = None
        self.setup_ui()

    def setup_ui(self):
        mme_col = [
            {"name": "drug", "label": "Drug", "field": "drug"},
            {"name": "dose", "label": "Dosage (mg)", "field": "dose"},
            {"name": "freq", "label": "Frequency (per day)", "field": "freq"},
            {"name": "cfactor", "label": "Conversion", "field": "cfactor"},
            {
                "name": "mme",
                "label": "MME",
                ":field": "row => row.dose * row.freq * row.cfactor",
                "default": 0,
            },
        ]

        with ui.column().classes("w-full items-center").style("align-items: center; padding: 10px"):
            ui.label("MME Calculator").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')
            table = ui.table(columns=mme_col, rows=self.mme_row, row_key="drug").style(
                "padding-top: 5px; padding-bottom: 10px; width: 700px"
            )

            table.add_slot(
                "header",
                """
                <q-tr :props="props">
                    <q-th
                        v-for="col in props.cols"
                        :key="col.name"
                        :props="props"
                        style="font-size: 14px"
                        class="text-center"
                    >
                        {{ col.label }}
                    </q-th>
                </q-tr>
                """,
            )
            table.add_slot(
                "body-cell-dose",
                """
                <q-td key="dose" :props="props">
                    <div class="full-width row justify-center items-center">
                        <q-input 
                            v-model.number="props.row.dose"
                            input-class="text-left"
                            type="number"
                            style="width: 75px; padding-top: 10px;"
                            dense 
                            @change="$parent.$emit('update-dose', props.row)"
                            :rules="[val => val > 0 || 'Dose must be greater than 0']"
                            autocomplete="off" />
                    </div>
                </q-td>
                """,
            )
            table.add_slot(
                "body-cell-freq",
                """
                <q-td key="freq" :props="props">
                    <div class="full-width row justify-center items-center">
                        <q-input 
                            v-model.number="props.row.freq"
                            input-class="text-left"
                            type="number"
                            style="width: 75px; padding-top: 10px;"
                            dense 
                            @change="$parent.$emit('update-dose', props.row)"
                            :rules="[val => val > 0 || 'Frequency must be greater than 0']"
                            autocomplete="off" />
                    </div>
                </q-td>
                """,
            )

            with table.add_slot("bottom-row"):
                with table.row():
                    with table.cell():
                        ui.label("")
                    with table.cell():
                        ui.label("")
                    with table.cell():
                        ui.label("")
                    with table.cell():
                        ui.label("Total MME:").classes("text-right")
                    with table.cell():
                        self.mme_total = (
                            ui.label(0)
                            .classes("items-right")
                            .style(
                                "background-color: #4caf50; border-radius: 5px; text-align: center; padding: 1px; margin-left: 20px"
                            )
                        )

            table.add_slot(
                "body-cell-mme",
                """
                <q-td key="mme" :props="props">
                    <q-badge 
                        :color="props.value > 200 ? 'red' : 'green'"
                        style="padding: 5px 11px"
                    >
                        {{ props.value }}
                    </q-badge>
                </q-td>
                """,
            )

            table.on("update-dose", self.update_dose)

    def update_dose(self, e):
        total_mme = 0.0
        for row in self.mme_row:
            if row["drug"] == e.args["drug"]:
                row["dose"] = float(e.args["dose"])
                row["freq"] = float(e.args["freq"])
                row["cfactor"] = float(e.args["cfactor"])
                row["mme"] = row["dose"] * row["freq"] * row["cfactor"]
                total_mme += row["mme"]

        self.mme_total.text = str(total_mme)
        if total_mme < 200:
            self.mme_total.style(
                "background-color: #4caf50; border-radius: 5px; text-align: center; padding: 1px;"
            )
        else:
            self.mme_total.style(
                "background-color: #f44336; border-radius: 5px; text-align: center; padding: 1px;"
            )


#%% ========== HPI Reword ========================================================================
class HPIReword:
    instances = {}

    def __init__(self):
        # Initialize UI components
        self.chat_int = None
        self.chat_out = None
        self.setup_ui()

    def setup_ui(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label("HPI Reword").style("font-weight: bold; font-size: 25px;")
            ui.separator().style('width: 85%')

            self.chat_int = ui.textarea('Current HPI Section').style("width: 750px")
            self.chat_out = ui.textarea('Reworded HPI Section').style("width: 750px").props('input-class=h-96')

            with ui.row():
                ui.button('Reword HPI', on_click=self.async_task).style("width:150px")
                ui.button('Reset', on_click=self.chat_reset).style("width:150px")

    async def async_task(self):
        spinner = ui.spinner(size='lg').classes("fixed top-0 left-0 right-0 bottom-0 m-auto")
        prompt = self.chat_int.value
        prompt = f"Revise the HPI (History of Present Illness) section of the SOAP note below to enhance clarity and accuracy. The revised HPI section should be single paragraph format. Do not remove content from the revised section that may be deemed or viewed as unnecessary; only reword or rephrase. Present the revised section first, and then provide a bulleted list detailing the specific changes and improvements made. Section: {prompt}"
        message = {'role': 'user', 'content': prompt}
        
        response = await AsyncClient().chat(model='llama3', messages=[message])
        spinner.set_visibility(False)
        self.chat_out.value = response['message']['content']

    def chat_reset(self):
        self.chat_int.value = ""
        self.chat_out.value = ""


#%% ========== HPI Info ==========================================================================
class HPIInfo:
    def __init__(self):
        # Initialize UI components
        self.patient_name = None
        self.patient_age = None
        self.reason_for_visit = None
        self.pain_level = None
        self.pain_type = None
        self.onset = None
        self.symp_1 = None
        self.symp_2 = None
        self.symp_3 = None
        self.symp_4 = None
        self.symp_5 = None
        self.symp_6 = None
        self.treatments_tried = None
        self.hpi_output = None

        self.setup_ui()

    def setup_ui(self):
        with ui.column().classes("w-full items-center").style("align-items: center;"):
            ui.label('Regular Visit Information').style("font-weight: bold; font-size: 25px; text-align: center;")
            ui.separator().style('width: 85%')

            with ui.column().classes('w-1/2').style('align-items: center; justify-content: center; margin: 0 auto;'):
                # Base Questions
                self.patient_name = ui.input('Patient Name', placeholder='John Doe').style('width: 90%; margin: 0 auto;')
                self.patient_age = ui.input('Patient Age', placeholder='25').style('width: 90%; margin: 0 auto;')
                self.reason_for_visit = ui.textarea('Reason for Visit', placeholder='What brings you in today?').style('width: 90%; margin: 0 auto;')

                # Pain Questions
                with ui.row().style('width: 90%; margin: 0 auto;'):
                    ui.label('Pain Level')
                    self.pain_level = ui.slider(min=0, max=10, value=0).props('label-always snap markers').style('padding-top: 15px')
                self.pain_type = ui.select(['Sharp', 'Dull', 'Aching', 'Burning', 'Other'], label='Pain Type').style('width: 90%; margin: 0 auto;')
                self.onset = ui.input('Onset of Problem', placeholder='When did the problem start?').style('width: 90%; margin: 0 auto;')

                # Symptom Questions
                ui.label('Do you have any of the following symptoms:').style("text-align: center;")
                with ui.grid(columns=2).style('width: 90%; border: 1.5px solid #CFCECF; margin: 0 auto;'):
                    self.symp_1 = ui.checkbox('Swelling')
                    self.symp_2 = ui.checkbox('Discoloration')

                    self.symp_3 = ui.checkbox('Post-static Pain')
                    self.symp_4 = ui.checkbox('Weakness')

                    self.symp_5 = ui.checkbox('Numbness')
                    self.symp_6 = ui.checkbox('Tingling')

                # Treatments Tried
                self.treatments_tried = ui.textarea('Treatments Tried', placeholder='What have you tried so far to alleviate the problem?').style('width: 90%; margin: 0 auto;')

                # Buttons
                with ui.row().style('justify-content: center;'):
                    ui.button('Submit', on_click=self.regular_visit_submit_data).style("width:150px")
                    ui.button('Reset', on_click=self.regular_visit_reset).style("width:150px")

                ui.separator()

                # HPI Output
                self.hpi_output = ui.textarea(label='HPI Output').style('width: 90%; height: 270px; margin: 0 auto;')

    def regular_visit_submit_data(self):
        hpi_text = f"""
        The patient, {self.patient_name.value}, is a {self.patient_age.value} year old who presents with a chief complaint of {self.reason_for_visit.value}. The patient reports that the problem started {self.onset.value} and has been experiencing {self.pain_type.value} pain with a severity of {self.pain_level.value}/10. The patient also reports {', '.join([symptom for symptom, value in [(f"Swelling", self.symp_1), (f"Discoloration", self.symp_2), (f"Post-static Pain", self.symp_3), (f"Weakness", self.symp_4), (f"Numbness", self.symp_5), (f"Tingling", self.symp_6)] if value.value]) or "no"} symptoms. The patient has tried the following treatments: {self.treatments_tried.value}.
        """
        self.hpi_output.value = hpi_text

    def regular_visit_reset(self):
        self.patient_name.value = ""
        self.patient_age.value = ""
        self.reason_for_visit.value = ""
        self.pain_level.value = 0
        self.pain_type.value = "Sharp"
        self.onset.value = ""
        self.symp_1.value = False
        self.symp_2.value = False
        self.symp_3.value = False
        self.symp_4.value = False
        self.symp_5.value = False
        self.symp_6.value = False
        self.treatments_tried.value = ""
        self.hpi_output.value = ""

#%% Office Forms ==================================================================================
class MedicalReferralForm:
    def __init__(self):
        # Get the user's desktop path
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Find the master PDF in the same directory as the script
        self.pdf_path = self.find_master_pdf()
        
        # Load provider information from CSV
        self.load_provider_data()
        
        # Initialize form fields
        self.form_fields = {
            'Patient': '',
            'Patient Diagnosis': '',
            'DOB': '',
            'Patient Insurance': '',
            'Provider Phone': '',
            'Patient Address': '',
            'Provider Specialty': '',
            'Patient Phone': '',
            'Provider Address': '',
            'Notes': '',
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Sex': '',
            'Provider': ''
        }
        
        # Store checkbox state
        self.gender = None
        
        # Reference to the main column for reset functionality
        self.column = None
        
        # Setup the UI
        self.setup_ui()
    
    def load_provider_data(self):
        """Load provider information from CSV"""
        try:
            # Find the CSV file in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, 'doctor_info.csv')
            
            # Read the CSV file
            self.providers_df = pd.read_csv(csv_path)
            
            # Create a full name column for easier searching
            self.providers_df['Full Name'] = self.providers_df['First'] + ' ' + self.providers_df['Last']
            
            # Create a list of full names for autocomplete
            self.provider_names = self.providers_df['Full Name'].tolist()
        except Exception as e:
            ui.notify(f'Error loading provider data: {str(e)}', type='negative')
            self.providers_df = pd.DataFrame()
            self.provider_names = []
    
    def find_provider_info(self, name):
        """Find provider information based on name"""
        if self.providers_df.empty:
            return None
        
        # Find matching providers (case-insensitive partial match)
        matches = self.providers_df[
            self.providers_df['Full Name'].str.contains(name, case=False, na=False)
        ]
        
        # Return the first match if found
        if not matches.empty:
            match = matches.iloc[0]
            return {
                'Provider': match['Full Name'],
                'Provider Specialty': match['Specialty'],
                'Provider Phone': match['Phone'],
                'Provider Address': f"{match['Street']}, {match['City']}, {match['State']} {match['Zip']}"
            }
        
        return None
    
    def setup_ui(self):
        # Main page layout
        with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4') as column:
            self.column = column
            
            # Initialize input fields list
            self.input_fields = []
            
            # Title at the top
            ui.label('Medical Referral Form').classes('text-2xl font-bold mb-4 self-center')
            
            # Patient and Provider Information in a grid
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Patient Information Column (Left)
                with ui.column().classes('w-full'):
                    ui.label('Patient Information').classes('text-xl font-semibold')
                    
                    # Patient Name
                    patient_name = ui.input(label='Patient Name', 
                                on_change=lambda e: self.update_field('Patient', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient_name)
                    
                    # Sex
                    sex_input = ui.input(label='Sex',
                                on_change=lambda e: self.update_field('Sex', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(sex_input)
                    
                    # Patient Diagnosis
                    patient_diagnosis = ui.input(label='Patient Diagnosis', 
                                on_change=lambda e: self.update_field('Patient Diagnosis', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient_diagnosis)
                    
                    # Date of Birth
                    with ui.input('Date of Birth', 
                                on_change=lambda e: self.update_field('DOB', e.value)) as dob:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date(mask='MM/DD/YYYY').bind_value(dob).props('default-view="Years"'):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                        with dob.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    self.input_fields.append(dob)
                    
                    # Patient Insurance
                    patient_insurance = ui.input(label='Patient Insurance', 
                                on_change=lambda e: self.update_field('Patient Insurance', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient_insurance)
                    
                    # Patient Phone
                    patient_phone = ui.input(label='Patient Phone', 
                                on_change=lambda e: self.update_field('Patient Phone', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient_phone)
                    
                    # Patient Address
                    patient_address = ui.input(label='Patient Address', 
                                on_change=lambda e: self.update_field('Patient Address', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient_address)
                
                # Provider Information Column (Right)
                with ui.column().classes('w-full'):
                    ui.label('Referring Provider Information').classes('text-xl font-semibold')
                    
                    # Provider Name with Autocomplete
                    provider_name = ui.input(
                        label='Provider Name', 
                        placeholder='Start typing provider name',
                        autocomplete=self.provider_names,
                        on_change=self.on_provider_name_change
                    ).classes('w-full')
                    
                    self.input_fields.append(provider_name)
                    self.provider_name_input = provider_name
                    
                    # Provider Specialty
                    provider_specialty = ui.input(label='Provider Specialty', 
                                on_change=lambda e: self.update_field('Provider Specialty', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(provider_specialty)
                    self.provider_specialty_input = provider_specialty
                    
                    # Provider Phone
                    provider_phone = ui.input(label='Provider Phone', 
                                on_change=lambda e: self.update_field('Provider Phone', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(provider_phone)
                    self.provider_phone_input = provider_phone
                    
                    # Provider Address
                    provider_address = ui.input(label='Provider Address', 
                                on_change=lambda e: self.update_field('Provider Address', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(provider_address)
                    self.provider_address_input = provider_address
            
            # Notes, Date, and Submit Section
            ui.label('Additional Information').classes('text-xl font-semibold mt-4')
            
            # Notes Textarea
            notes = ui.textarea(label='Notes', 
                        on_change=lambda e: self.update_field('Notes', e.value)) \
                .classes('w-full')
            self.input_fields.append(notes)
            
            # Date Input
            with ui.input('Date',
                        on_change=lambda e: self.update_field('Date', e.value)) as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date(mask='MM/DD/YYYY').bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('Today', on_click=lambda: date.set_value(datetime.now().strftime('%m/%d/%Y'))).props('flat')
                            ui.button('Close', on_click=menu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            self.input_fields.append(date)
            
            # Create a column to hold the buttons
            with ui.row().classes('w-full justify-center items-center gap-4'):
                ui.button('Submit and Save Form', 
                        on_click=self.submit_form,
                        color='primary') \
                    .classes('w-25')
                
                ui.button('Reset Form', 
                        on_click=self.reset_form,
                        color='negative') \
                    .classes('w-25')
                
    def on_provider_name_change(self, e):
        """Handle provider name input changes"""
        name = e.value.strip()
        self.update_field('Provider', name)
        
        # Try to find and auto-populate provider information
        provider_info = self.find_provider_info(name)
        if provider_info:
            # Automatically fill in other provider fields
            self.provider_specialty_input.value = provider_info['Provider Specialty']
            self.update_field('Provider Specialty', provider_info['Provider Specialty'])
            
            self.provider_phone_input.value = provider_info['Provider Phone']
            self.update_field('Provider Phone', provider_info['Provider Phone'])
            
            self.provider_address_input.value = provider_info['Provider Address']
            self.update_field('Provider Address', provider_info['Provider Address'])

    def select_provider(self, full_name):
        """Select a provider from the suggestions"""
        # Set the full name in the input
        self.provider_name_input.value = full_name
        self.update_field('Provider', full_name)
        
        # Close suggestions
        self.provider_suggestions.close()
        
        # Find and populate provider details
        provider_info = self.find_provider_info(full_name)
        if provider_info:
            # Automatically fill in other provider fields
            self.provider_specialty_input.value = provider_info['Provider Specialty']
            self.update_field('Provider Specialty', provider_info['Provider Specialty'])
            
            self.provider_phone_input.value = provider_info['Provider Phone']
            self.update_field('Provider Phone', provider_info['Provider Phone'])
            
            self.provider_address_input.value = provider_info['Provider Address']
            self.update_field('Provider Address', provider_info['Provider Address'])

    def find_provider_info(self, name):
        """Find provider information based on name"""
        if self.providers_df.empty:
            return None
        
        # Find matching providers (exact match)
        matches = self.providers_df[
            self.providers_df['Full Name'] == name
        ]
        
        # Return the first match if found
        if not matches.empty:
            match = matches.iloc[0]
            return {
                'Provider': match['Full Name'],
                'Provider Specialty': match['Specialty'],
                'Provider Phone': match['Phone'],
                'Provider Address': f"{match['Street']}, {match['City']}, {match['State']} {match['Zip']}"
            }
        
        return None

    def find_master_pdf(self):
        """Find the Referral.pdf in the same directory as the script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, 'Forms/Referral.pdf')
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Referral.pdf not found in the script's directory")
        
        return pdf_path
    
    def update_field(self, field, value):
        """Update a specific form field"""
        self.form_fields[field] = value
    
    def submit_form(self):
        """Handle form submission and PDF filling"""
        try:
            # Create an in-memory PDF
            pdf_buffer = io.BytesIO()
            
            # Open the PDF
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Get the first page
                page = pdf_reader.pages[0]
                pdf_writer.add_page(page)
                
                # Update text fields first
                text_fields = {k: v for k, v in self.form_fields.items() 
                            if k not in ['Male', 'Female']}
                pdf_writer.update_page_form_field_values(
                    pdf_writer.pages[0], 
                    text_fields
                )
                
                # Generate filename
                output_filename = f'Referral_Form_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                # Write to the in-memory buffer
                pdf_writer.write(pdf_buffer)
                pdf_buffer.seek(0)
            
            # Create a download button that opens the PDF in a new tab
            def download_pdf():
                ui.download(
                    pdf_buffer.getvalue(), 
                    filename=output_filename, 
                    media_type='application/pdf'
                )
            
            # Show success dialog with download option
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label('Form Submission').classes('text-lg font-bold')
                    ui.label('Form successfully prepared').classes('mb-4')
                    ui.button('Download PDF', on_click=download_pdf).classes('mt-4')
                    ui.button('Close', on_click=dialog.close).classes('mt-2')
            
            dialog.open()
        
        except Exception as e:
            ui.notify(f'Error preparing form: {str(e)}', type='negative')

    def reset_form(self):
        """Reset all form fields to their default state"""
        # Reset form fields to initial values
        self.form_fields = {
            'Patient': '',
            'Patient Diagnosis': '',
            'DOB': '',
            'Patient Insurance': '',
            'Provider Phone': '',
            'Patient Address': '',
            'Provider Specialty': '',
            'Patient Phone': '',
            'Provider Address': '',
            'Notes': '',
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Sex': '',
            'Provider': ''
        }

        # Reset all stored input fields
        for field in self.input_fields:
            field.value = ''

        # Notify user
        ui.notify('Form has been reset', type='info')

class LetterheadForm:
    def __init__(self):
        # Get the user's desktop path
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Find the letterhead PDF in the same directory as the script
        self.pdf_path = self.find_letterhead_pdf()
        
        # Initialize form fields
        self.form_fields = {
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Body Text': ''
        }
        
        # Store input fields for reset functionality
        self.input_fields = []
        
        # Setup the UI
        self.setup_ui()
    
    def find_letterhead_pdf(self):
        """Find the Letterhead.pdf in the same directory as the script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, 'Forms/Letterhead.pdf')
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Letterhead.pdf not found in the script's directory")
        
        return pdf_path
    
    def setup_ui(self):
        # Main column for Letterhead Form
        with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
            # Title
            ui.label('Letterhead Form').classes('text-2xl font-bold mb-4 self-center')
            
            # Date Input
            with ui.input('Date', 
                        on_change=lambda e: self.update_field('Date', e.value)) as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date(mask='MM/DD/YYYY').bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('Today', on_click=lambda: date.set_value(datetime.now().strftime('%m/%d/%Y'))).props('flat')
                            ui.button('Close', on_click=menu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            self.input_fields.append(date)
            
            # Body Text Textarea
            body_text = ui.textarea(label='Body Text', 
                        on_change=lambda e: self.update_field('Body Text', e.value)) \
                .classes('w-full h-64')
            self.input_fields.append(body_text)
            
            # Buttons Row
            with ui.row().classes('w-full justify-center items-center gap-4'):
                ui.button('Submit and Save Letterhead', 
                        on_click=self.submit_form,
                        color='primary') \
                    .classes('w-25')
                
                ui.button('Reset Form', 
                        on_click=self.reset_form,
                        color='negative') \
                    .classes('w-25')
    
    def update_field(self, field, value):
        """Update a specific form field"""
        self.form_fields[field] = value
    
    def submit_form(self):
        """Handle form submission and PDF filling"""
        try:
            # Create an in-memory PDF
            pdf_buffer = io.BytesIO()
            
            # Open the PDF
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Get the first page
                page = pdf_reader.pages[0]
                pdf_writer.add_page(page)
                
                # Update text fields
                pdf_writer.update_page_form_field_values(
                    pdf_writer.pages[0], 
                    self.form_fields
                )
                
                # Generate filename
                output_filename = f'Letterhead_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                # Write to the in-memory buffer
                pdf_writer.write(pdf_buffer)
                pdf_buffer.seek(0)
            
            # Create a download button that opens the PDF in a new tab
            def download_pdf():
                ui.download(
                    pdf_buffer.getvalue(), 
                    filename=output_filename, 
                    media_type='application/pdf'
                )
            
            # Show success dialog with download option
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label('Letterhead Form').classes('text-lg font-bold')
                    ui.label('Form successfully prepared').classes('mb-4')
                    ui.button('Download PDF', on_click=download_pdf).classes('mt-4')
                    ui.button('Close', on_click=dialog.close).classes('mt-2')
            
            dialog.open()
        
        except Exception as e:
            ui.notify(f'Error preparing letterhead: {str(e)}', type='negative')
    
    def reset_form(self):
        """Reset all form fields to their default state"""
        # Reset form fields to initial values
        self.form_fields = {
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Body Text': ''
        }

        # Reset all stored input fields
        for field in self.input_fields:
            field.value = ''

        # Notify user
        ui.notify('Letterhead form has been reset', type='info')

class ExcuseForm:
    def __init__(self):
        # Get the user's desktop path
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Find the PDF in the same directory as the script
        self.pdf_path = self.find_form_pdf()
        
        # Initialize form fields
        self.form_fields = {
            'date1': datetime.now().strftime('%m/%d/%Y'),
            'date2': datetime.now().strftime('%m/%d/%Y'),
            'date3': datetime.now().strftime('%m/%d/%Y'),
            'limitations': '',
            'dob': '',
            'notes': '',
            'visit_reason': '',
            'patient1': '',
            'patient2': '',
            'patient3': ''
        }
        
        # Store input fields for reset functionality
        self.input_fields = []
        
        # Setup the UI
        self.setup_ui()
    
    def find_form_pdf(self):
        """Find the Form3.pdf in the same directory as the script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, 'Forms/Excuse_Note.pdf')
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Excuse_Note.pdf not found in the script's directory")
        
        return pdf_path
    
    def update_all_dates(self, value):
        """Update all date fields with the same value"""
        self.form_fields['date1'] = value
        self.form_fields['date2'] = value
        self.form_fields['date3'] = value
        
        # Update all date input fields
        for field in self.date_inputs:
            field.value = value
    
    def update_all_patients(self, value):
        """Update all patient fields with the same value"""
        self.form_fields['patient1'] = value
        self.form_fields['patient2'] = value
        self.form_fields['patient3'] = value
        
        # Update all patient input fields
        for field in self.patient_inputs:
            field.value = value
    
    def setup_ui(self):
        # Main column for Form
        with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
            # Title
            ui.label('Excuse Note').classes('text-2xl font-bold mb-4 self-center')
            
            # Store date and patient inputs for synchronization
            self.date_inputs = []
            self.patient_inputs = []
            
            # Create a grid layout for the form
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Left Column
                with ui.column().classes('w-full'):
                    # Date Input (will sync all dates)
                    with ui.input('Date', 
                                on_change=lambda e: self.update_all_dates(e.value)) as date:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date(mask='MM/DD/YYYY').bind_value(date):
                                with ui.row().classes('justify-end'):
                                    ui.button('Today', 
                                            on_click=lambda: self.update_all_dates(
                                                datetime.now().strftime('%m/%d/%Y'))).props('flat')
                                    ui.button('Close', on_click=menu.close).props('flat')
                            with date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    self.input_fields.append(date)
                    self.date_inputs.extend([date])
                    
                    # Patient Name (will sync all patient fields)
                    patient = ui.input(label='Patient Name',
                                     on_change=lambda e: self.update_all_patients(e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient)
                    self.patient_inputs.extend([patient])
                    
                    # Date of Birth
                    with ui.input('Date of Birth',
                                on_change=lambda e: self.update_field('dob', e.value)) as dob:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date(mask='MM/DD/YYYY').bind_value(dob):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                            with dob.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    self.input_fields.append(dob)
                
                # Right Column
                with ui.column().classes('w-full'):
                    # Limitations
                    limitations = ui.textarea(label='Limitations',
                                           on_change=lambda e: self.update_field('limitations', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(limitations)
                    
                    # Visit Reason
                    visit_reason = ui.textarea(label='Reason for Visit',
                                            on_change=lambda e: self.update_field('visit_reason', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(visit_reason)
            
            # Notes Section (Full Width)
            notes = ui.textarea(label='Additional Notes',
                             on_change=lambda e: self.update_field('notes', e.value)) \
                .classes('w-full')
            self.input_fields.append(notes)
            
            # Buttons Row
            with ui.row().classes('w-full justify-center items-center gap-4'):
                ui.button('Submit and Save Form',
                        on_click=self.submit_form,
                        color='primary') \
                    .classes('w-25')
                
                ui.button('Reset Form',
                        on_click=self.reset_form,
                        color='negative') \
                    .classes('w-25')
    
    def update_field(self, field, value):
        """Update a specific form field"""
        self.form_fields[field] = value
    
    def submit_form(self):
        """Handle form submission and PDF filling"""
        try:
            # Create an in-memory PDF
            pdf_buffer = io.BytesIO()
            
            # Open the PDF
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Get the first page
                page = pdf_reader.pages[0]
                pdf_writer.add_page(page)
                
                # Update text fields
                pdf_writer.update_page_form_field_values(
                    pdf_writer.pages[0], 
                    self.form_fields
                )
                
                # Generate filename
                output_filename = f'Form3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                # Write to the in-memory buffer
                pdf_writer.write(pdf_buffer)
                pdf_buffer.seek(0)
            
            # Create a download button that opens the PDF in a new tab
            def download_pdf():
                ui.download(
                    pdf_buffer.getvalue(), 
                    filename=output_filename, 
                    media_type='application/pdf'
                )
            
            # Show success dialog with download option
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label('Form Three').classes('text-lg font-bold')
                    ui.label('Form successfully prepared').classes('mb-4')
                    ui.button('Download PDF', on_click=download_pdf).classes('mt-4')
                    ui.button('Close', on_click=dialog.close).classes('mt-2')
            
            dialog.open()
        
        except Exception as e:
            ui.notify(f'Error preparing form: {str(e)}', type='negative')
    
    def reset_form(self):
        """Reset all form fields to their default state"""
        # Reset form fields to initial values
        self.form_fields = {
            'date1': datetime.now().strftime('%m/%d/%Y'),
            'date2': datetime.now().strftime('%m/%d/%Y'),
            'date3': datetime.now().strftime('%m/%d/%Y'),
            'limitations': '',
            'dob': '',
            'notes': '',
            'visit_reason': '',
            'patient1': '',
            'patient2': '',
            'patient3': ''
        }

        # Reset all stored input fields
        for field in self.input_fields:
            field.value = ''

        # Notify user
        ui.notify('Form has been reset', type='info')

class PhysicalTherapyForm:
    def __init__(self):
        # Get the user's desktop path
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Find the PDF in the same directory as the script
        self.pdf_path = self.find_form_pdf()
        
        # Initialize form fields
        self.form_fields = {
            'phone': '',
            'address': '',
            'patient': '',
            'dob': '',
            'notes': '',
            'date': datetime.now().strftime('%m/%d/%Y'),
            'treatment': '',
            'diagnosis': '',
            'sex': '',
            'pt_frequency': '',
            'pt_duration': ''
        }
        
        # Store input fields for reset functionality
        self.input_fields = []
        
        # Setup the UI
        self.setup_ui()
    
    def find_form_pdf(self):
        """Find the PT_Order.pdf in the same directory as the script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, 'Forms/PT_Order.pdf')
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("PT_Order.pdf not found in the script's directory")
        
        return pdf_path
    
    def setup_ui(self):
        # Main column for Form
        with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
            # Title
            ui.label('Physical Therapy Order Form').classes('text-2xl font-bold mb-4 self-center')
            
            # Create a grid layout for the form
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Left Column
                with ui.column().classes('w-full'):
                    # Patient Name
                    patient = ui.input(label='Patient Name',
                                     on_change=lambda e: self.update_field('patient', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient)
                    
                    # Sex
                    sex = ui.input(label='Sex',
                                  on_change=lambda e: self.update_field('sex', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(sex)
                    
                    # Date of Birth
                    with ui.input('Date of Birth',
                                on_change=lambda e: self.update_field('dob', e.value)) as dob:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date(mask='MM/DD/YYYY').bind_value(dob):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                            with dob.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    self.input_fields.append(dob)
                    
                    # Phone
                    phone = ui.input(label='Phone',
                                    on_change=lambda e: self.update_field('phone', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(phone)

                    # Address
                    address = ui.input(label='Address',
                                      on_change=lambda e: self.update_field('address', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(address)
                
                # Right Column
                with ui.column().classes('w-full'):                  
                    # Diagnosis
                    diagnosis = ui.input(label='Diagnosis',
                                        on_change=lambda e: self.update_field('diagnosis', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(diagnosis)
                    
                    # Treatment
                    treatment = ui.input(label='Treatment',
                                        on_change=lambda e: self.update_field('treatment', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(treatment)
                    
                    # PT Frequency
                    pt_frequency = ui.input(label='PT Frequency',
                                           on_change=lambda e: self.update_field('pt_frequency', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(pt_frequency)
                    
                    # PT Duration
                    pt_duration = ui.input(label='PT Duration',
                                          on_change=lambda e: self.update_field('pt_duration', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(pt_duration)
            
            # Date Input
            with ui.input('Date',
                        on_change=lambda e: self.update_field('date', e.value)) as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date(mask='MM/DD/YYYY').bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('Today', on_click=lambda: date.set_value(datetime.now().strftime('%m/%d/%Y'))).props('flat')
                            ui.button('Close', on_click=menu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            self.input_fields.append(date)
            
            # Notes Section
            notes = ui.textarea(label='Additional Notes',
                             on_change=lambda e: self.update_field('notes', e.value)) \
                .classes('w-full')
            self.input_fields.append(notes)
            
            # Buttons Row
            with ui.row().classes('w-full justify-center items-center gap-4'):
                ui.button('Submit and Save Form',
                        on_click=self.submit_form,
                        color='primary') \
                    .classes('w-25')
                
                ui.button('Reset Form',
                        on_click=self.reset_form,
                        color='negative') \
                    .classes('w-25')
    
    def update_field(self, field, value):
        """Update a specific form field"""
        self.form_fields[field] = value
    
    def submit_form(self):
        """Handle form submission and PDF filling"""
        try:
            # Create an in-memory PDF
            pdf_buffer = io.BytesIO()
            
            # Open the PDF
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Get the first page
                page = pdf_reader.pages[0]
                pdf_writer.add_page(page)
                
                # Update text fields
                pdf_writer.update_page_form_field_values(
                    pdf_writer.pages[0], 
                    self.form_fields
                )
                
                # Generate filename
                output_filename = f'PT_Order_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                # Write to the in-memory buffer
                pdf_writer.write(pdf_buffer)
                pdf_buffer.seek(0)
            
            # Create a download button that opens the PDF in a new tab
            def download_pdf():
                ui.download(
                    pdf_buffer.getvalue(), 
                    filename=output_filename, 
                    media_type='application/pdf'
                )
            
            # Show success dialog with download option
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label('Physical Therapy Order Form').classes('text-lg font -bold')
                    ui.label('Form successfully prepared').classes('mb-4')
                    ui.button('Download PDF', on_click=download_pdf).classes('mt-4')
                    ui.button('Close', on_click=dialog.close).classes('mt-2')
            
            dialog.open()
        
        except Exception as e:
            ui.notify(f'Error preparing form: {str(e)}', type='negative')

    def reset_form(self):
        """Reset all form fields to their default state"""
        # Reset form fields to initial values
        self.form_fields = {
            'phone': '',
            'address': '',
            'patient': '',
            'dob': '',
            'notes': '',
            'date': datetime.now().strftime('%m/%d/%Y'),
            'treatment': '',
            'diagnosis': '',
            'sex': '',
            'pt_frequency': '',
            'pt_duration': ''
        }

        # Reset all stored input fields
        for field in self.input_fields:
            field.value = ''

        # Notify user
        ui.notify('Physical Therapy Order Form has been reset', type='info')

class LabOrderForm:
    def __init__(self):
        # Get the user's desktop path
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Find the PDF in the same directory as the script
        self.pdf_path = self.find_form_pdf()
        
        # Initialize form fields
        self.form_fields = {
            'phone': '',
            'address': '',
            'note': '',
            'order': '',
            'dob': '',
            'insurance': '',
            'patient': '',
            'date': datetime.now().strftime('%m/%d/%Y'),
            'diagnosis': '',
            'sex': ''
        }
        
        # Store input fields for reset functionality
        self.input_fields = []
        
        # Setup the UI
        self.setup_ui()
    
    def find_form_pdf(self):
        """Find the Lab_Order.pdf in the same directory as the script"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, 'Forms/Lab_Order.pdf')
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Lab_Order.pdf not found in the script's directory")
        
        return pdf_path
    
    def setup_ui(self):
        # Main column for Form
        with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
            # Title
            ui.label('Lab Order Form').classes('text-2xl font-bold mb-4 self-center')
            
            # Create a grid layout for the form
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Left Column
                with ui.column().classes('w-full'):
                    # Patient Name
                    patient = ui.input(label='Patient Name',
                                       on_change=lambda e: self.update_field('patient', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(patient)
                    
                    # Sex
                    sex = ui.input(label='Sex',
                                   on_change=lambda e: self.update_field('sex', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(sex)
                    
                    # Date of Birth
                    with ui.input('Date of Birth',
                                  on_change=lambda e: self.update_field('dob', e.value)) as dob:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date(mask='MM/DD/YYYY').bind_value(dob):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                            with dob.add_slot('append'):
                                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    self.input_fields.append(dob)
                    
                    # Phone
                    phone = ui.input(label='Phone',
                                     on_change=lambda e: self.update_field('phone', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(phone)

                    # Address
                    address = ui.input(label='Address',
                                       on_change=lambda e: self.update_field('address', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(address)
                
                # Right Column
                with ui.column().classes('w-full'):                  
                    # Diagnosis
                    diagnosis = ui.input(label='Diagnosis',
                                         on_change=lambda e: self.update_field('diagnosis', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(diagnosis)
                    
                    # Insurance
                    insurance = ui.input(label='Insurance',
                                         on_change=lambda e: self.update_field('insurance', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(insurance)
                    
                     # Order (Multi-select and Additional Tests)
                    with ui.column().classes('w-full'):
                        # Multi-select for Tests
                        order_select = ui.select(label='Order (Select Tests)',
                                                  multiple=True,
                                                  options=[
                                                      'CBC with Differential',
                                                      'CBC without Differential',
                                                      'Erythrocyte Sedimentation Rate',
                                                      'C-Reactive Protein',
                                                      'Basic Metabolic Panel',
                                                      'Uric Acid',
                                                      'Comprehensive Metabolic Panel',
                                                      'Rheumatoid Factor',
                                                      'Vitamin B12',
                                                      'Anti-Nuclear Antibody',
                                                      'Vitamin D',
                                                      'OGTT (#090415 LabCorp)',
                                                      'HgA1c',
                                                      'Insulin Assay'
                                                  ],
                                                  on_change=lambda e: self.update_order_field(order_select.value or [], additional_tests.value)) \
                            .classes('w-full')
                        self.input_fields.append(order_select)

                        # Additional Tests Input
                        additional_tests = ui.input(label='Additional Tests (comma-separated)',
                                                     on_change=lambda e: self.update_order_field(order_select.value or [], e.value)) \
                            .classes('w-full')
                        self.input_fields.append(additional_tests)
                    
                    # Notes Section
                    notes = ui.textarea(label='Notes',
                                         on_change=lambda e: self.update_field('note', e.value)) \
                        .classes('w-full')
                    self.input_fields.append(notes)
            
            # Date Input
            with ui.input('Date',
                          on_change=lambda e: self.update_field('date', e.value)) as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date(mask='MM/DD/YYYY').bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('Today', on_click=lambda: date.set_value(datetime.now().strftime('%m/%d/%Y'))).props('flat')
                            ui.button('Close', on_click=menu.close).props('flat')
                    with date.add_slot('append'):
                        ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            self.input_fields.append(date)
            
            # Buttons Row
            with ui.row().classes('w-full justify-center items-center gap-4'):
                ui.button('Submit and Save Form',
                          on_click=self.submit_form,
                          color='primary') \
                    .classes('w-25')
                
                ui.button('Reset Form',
                          on_click=self.reset_form,
                          color='negative') \
                    .classes('w-25')
    
    def update_field(self, field, value):
        """Update a specific form field"""
        self.form_fields[field] = value

    def update_order_field(self, selected_tests, additional_tests):
        """Update the order field with selected tests and additional tests"""
        # Ensure selected_tests is a list
        if selected_tests is None:
            selected_tests = []
        
        combined_order = ', '.join(selected_tests)
        if additional_tests:
            combined_order += ', ' + additional_tests
        self.form_fields['order'] = combined_order.strip()
    
    def update_additional_tests(self, value):
        """Update the additional tests field"""
        self.form_fields['additional_tests'] = value
    
    def submit_form(self):
        """Handle form submission and PDF filling"""
        try:
            # Create an in-memory PDF
            pdf_buffer = io.BytesIO()
            
            # Open the PDF
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Get the first page
                page = pdf_reader.pages[0]
                pdf_writer.add_page(page)
                
                # Update text fields
                pdf_writer.update_page_form_field_values(
                    pdf_writer.pages[0], 
                    self.form_fields
                )
                
                # Generate filename
                output_filename = f'Lab_Order_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                # Write to the in-memory buffer
                pdf_writer.write(pdf_buffer)
                pdf_buffer.seek(0)
            
            # Create a download button that opens the PDF in a new tab
            def download_pdf():
                ui.download(
                    pdf_buffer.getvalue(), 
                    filename=output_filename, 
                    media_type='application/pdf'
                )
            
            # Show success dialog with download option
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label('Lab Order Form').classes('text-lg font-bold')
                    ui.label('Form successfully prepared').classes('mb-4')
                    ui.button('Download PDF', on_click=download_pdf).classes('mt-4')
                    ui.button('Close', on_click=dialog.close).classes('mt-2')
            
            dialog.open()
        
        except Exception as e:
            ui.notify(f'Error preparing form: {str(e)}', type='negative')

    def reset_form(self):
        """Reset all form fields to their default state"""
        # Reset form fields to initial values
        self.form_fields = {
            'phone': '',
            'address': '',
            'note': '',
            'order': '',
            'dob': '',
            'insurance': '',
            'patient': '',
            'date': datetime.now().strftime('%m/%d/%Y'),
            'diagnosis': '',
            'sex': '',
            'additional_tests': ''
        }

        # Reset all stored input fields
        for field in self.input_fields:
            field.value = ''

        # Notify user
        ui.notify('Lab Order Form has been reset', type='info')

class OfficeFormsMain:
    def __init__(self):
        with ui.column().classes("w-full h-full items-center").style("align-items: center;"):
            ui.label('Office Forms').style("font-weight: bold; font-size: 25px; text-align: center;")
            ui.separator().style('width: 85%')

            # Sub tabs for each form
            with ui.tabs().classes('w-full h-12').props('indicator-color="primary" active-color="primary" inline-label') as form_sub_tabs:
                ref_form = ui.tab("Referral Form")
                letterhead_form = ui.tab("Letterhead")
                excuse_form = ui.tab("Excuse Note")
                pt_order_form = ui.tab("PT Order")
                lab_order_form = ui.tab("Lab Order")

            # Sub tab panels
            with ui.tab_panels(form_sub_tabs, value=ref_form).classes("w-full h-full grow").props('transition-prev=jump-up transition-next=jump-down'):
                with ui.tab_panel(ref_form).classes("w-full h-full"):
                    MedicalReferralForm()
                
                with ui.tab_panel(letterhead_form).classes("w-full h-full"):
                    LetterheadForm()
                
                with ui.tab_panel(excuse_form).classes("w-full h-full"):
                    ExcuseForm()

                with ui.tab_panel(pt_order_form).classes("w-full h-full"):
                    PhysicalTherapyForm()

                with ui.tab_panel(lab_order_form).classes("w-full h-full"):
                    LabOrderForm()

#%% Main Program =================================================================================

@ui.page("/")  # Make each instance independent
def main_page():
    ui.query('.nicegui-content').classes('p-0 w-full')
    ui.query('.q-page').classes('flex')
    with ui.header().classes('h-16', replace='row items-center').style('background-color: #141414; border-bottom: 1px solid #606060;') as header:
        ui.button(on_click=lambda: left_drawer.toggle(),
                icon='menu').props('flat color=white size=18px').style('padding-left: 25px;')
        ui.space()
        ui.label('Clinical Tool Hub').style('font-size: 25px; font-weight: bold; padding-right: 25px;')
    with ui.left_drawer().classes('w-full').props('width=235').style('background-color: #121212; border-right: 1px solid #606060;') as left_drawer:
        # Icons from google icons
        with ui.tabs().classes("w-full h-full").props('vertical indicator-color="primary" active-color="primary" inline-label') as tabs:
            icd_look_tab = ui.tab("ICD10 Lookup", icon="code").classes('justify-start')
            ins_glu_tab = ui.tab("Insulin & GTT", icon="water_drop").classes('justify-start')
            wound_track_tab = ui.tab("Wound Tracker", icon="healing").classes('justify-start')
            cost_est_tab = ui.tab("Cost Estimator", icon="paid").classes('justify-start')
            npi_look_tab = ui.tab("NPI Lookup", icon="person_search").classes('justify-start')
            dr_rep_look_tab = ui.tab("Info Lookup", icon="contacts").classes('justify-start')
            mme_calc_tab = ui.tab("MME Calculator", icon="medication").classes('justify-start')
            hpi_reword = ui.tab("HPI Reword", icon="edit").classes('justify-start')
            hpi_info = ui.tab('HPI Info', icon='history_edu').classes('justify-start')
            office_forms = ui.tab('Office Forms', icon='description').classes('justify-start')

    #%% App Tabs ==================================================================================
    # Transitions ex: jump-up, jump-left, etc. fade, scale
    with ui.tab_panels(tabs, value=icd_look_tab).classes("w-full h-full").props('transition-prev=jump-up transition-next=jump-down'):
        with ui.tab_panel(icd_look_tab).classes('w-full h-full'):
            icd_lookup_instance = ICDLookup()
            icd_lookup_instance.ICD_UI_SetUp()

        with ui.tab_panel(ins_glu_tab).classes('w-full h-full'):
            insulin_glucose_plot_instance = InsulinGlucosePlot()
            insulin_glucose_plot_instance.InsGlu_UI_Setup()

        with ui.tab_panel(wound_track_tab).classes('w-full h-full'):
            wound_tracker_instance = WoundTracker()
            wound_tracker_instance.woundtracker_UI_Setup()

        with ui.tab_panel(cost_est_tab).classes('w-full h-full'):
            cost_estimator_instance = CostEstimator()
            cost_estimator_instance.cost_estimator_UI_Setup()
        
        with ui.tab_panel(npi_look_tab).classes('w-full h-full'):
            npi_lookup_instance = NPILookup()

        with ui.tab_panel(dr_rep_look_tab).classes('w-full h-full'):
            info_lookup_instance = InfoLookup()

        with ui.tab_panel(mme_calc_tab).classes('w-full h-full'):
            mme_calculator_instance = MMECalculator()

        with ui.tab_panel(hpi_reword).classes('w-full h-full'):
            hpi_reword_instance = HPIReword()

        with ui.tab_panel(hpi_info).classes('w-full h-full'):
            hpi_info_instance = HPIInfo()

        with ui.tab_panel(office_forms).classes('w-full h-full'):
            office_forms_instance = OfficeFormsMain()

    #%% App Footer ===============================================================================
    ui.add_head_html('''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>
    <style>
        button.s-btn1:hover {
            background-color: #3b5998 !important;
            transition-duration: 0.5s;
        }
        button.s-btn2:hover {
            background-color: #00aced !important;
            transition-duration: 0.5s;
        }
        button.s-btn3:hover {
            background-color: #2b3137 !important;
            transition-duration: 0.5s;
        }
        button.s-btn4:hover {
            background-color: #0077B5 !important;
            transition-duration: 0.5s;
        }              
    </style>
    ''')
    with ui.footer().style("background-color: #26272b; align-items: center;").classes('w-full'):
        # Add copyright text
        ui.label('Copyright © 2024 All Rights Reserved by ')
        ui.link('Vortex Design', target="_blank", new_tab=True).style(
            "color: #6FA5D8; transform: translateX(-10px)")
        ui.space()

        # Create a row for social icons
        with ui.row().style("justify-content: flex-end; margin-right: 10px;"):
            ui.button(icon='fa fa-facebook', on_click=lambda: ui.navigate.to('https://www.facebook.com/', new_tab=True)).style(
                "background-color: #33353d; color: white; border-radius: 50%; width: 35px; height: 35px;").classes("s-btn1")

            ui.button(icon='fa fa-twitter', on_click=lambda: ui.navigate.to('https://www.twitter.com/', new_tab=True)).style(
                "background-color: #33353d; color: white; border-radius: 50%; width: 35px; height: 35px; margin-left: 6px;").classes("s-btn2")

            ui.button(icon='fa fa-github', on_click=lambda: ui.navigate.to('https://www.github.com/', new_tab=True)).style(
                "background-color: #33353d; color: white; border-radius: 50%; width: 35px; height: 35px; margin-left: 6px;").classes("s-btn3")

            ui.button(icon='fa fa-linkedin', on_click=lambda: ui.navigate.to('https://www.linkedin.com/', new_tab=True)).style(
                "background-color: #33353d; color: white; border-radius: 50%; width: 35px; height: 35px; margin-left: 6px;").classes("s-btn4")


#%% Window Setup =================================================================================
# Print url's to terminal using colors using ANSI escape codes
    # https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
    # \033[31m	Red         \033[36m  Cyan
    # \033[32m	Green
    # \033[33m	Yellow
    # \033[34m	Blue        \033[0m   Reset color & style
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"
UNDERLINE = "\033[4m"
app.on_startup(lambda: print(
    f'{GREEN}Thanks for using our app from Vortex Design.\n' +
    f'App available at one of these URLs:{RESET}\n' + 
    '\n'.join(f'{CYAN}{UNDERLINE}' + url + f'{RESET}' for url in app.urls if not url.startswith('http://localhost'))
    ))
# Base64 image for site icon
fav_icon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAEtGlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS41LjAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iCiAgICB4bWxuczpleGlmPSJodHRwOi8vbnMuYWRvYmUuY29tL2V4aWYvMS4wLyIKICAgIHhtbG5zOnBob3Rvc2hvcD0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3Nob3AvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIgogICAgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIKICAgdGlmZjpJbWFnZUxlbmd0aD0iMjQiCiAgIHRpZmY6SW1hZ2VXaWR0aD0iMjQiCiAgIHRpZmY6UmVzb2x1dGlvblVuaXQ9IjIiCiAgIHRpZmY6WFJlc29sdXRpb249IjcyLzEiCiAgIHRpZmY6WVJlc29sdXRpb249IjcyLzEiCiAgIGV4aWY6UGl4ZWxYRGltZW5zaW9uPSIyNCIKICAgZXhpZjpQaXhlbFlEaW1lbnNpb249IjI0IgogICBleGlmOkNvbG9yU3BhY2U9IjEiCiAgIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiCiAgIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIKICAgeG1wOk1vZGlmeURhdGU9IjIwMjQtMDItMDZUMTA6NTU6MjAtMDc6MDAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQtMDItMDZUMTA6NTU6MjAtMDc6MDAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJwcm9kdWNlZCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWZmaW5pdHkgRGVzaWduZXIgMiAyLjAuMyIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0wMi0wNlQxMDo1NToyMC0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgo8P3hwYWNrZXQgZW5kPSJyIj8+VeB+KAAAAX9pQ0NQc1JHQiBJRUM2MTk2Ni0yLjEAACiRdZHPK0RRFMc/ZjBihFhYWLyEFcLUxEaZSUNJGqMMNm+eNzNqfrzee5Jsle0UJTZ+LfgL2CprpYiUrK2JDXrOM2okc27nns/93ntO954LnlhGy1qVfZDN2WY0ElJm43OK7wkP1TQRJKBqljEyNTVBWXu7pcKN1z1urfLn/rW6Rd3SoKJGeFgzTFt4THhixTZc3hJu0dLqovCJcLcpFxS+cfVEkZ9cThX5w2UzFg2Dp1FYSf3ixC/W0mZWWF5ORzazrP3cx32JX8/NTEtsF2/DIkqEEArjjBKWnvQzJHOQHgbolRVl8vu+8yfJS64ms8EqJkukSGPTLeqyVNclJkXXZWRYdfv/t69WMjBQrO4PQdWj47x0gm8TPguO837gOJ+H4H2A81wpP78Pg6+iF0paxx40rMPpRUlLbMPZBrTeG6qpfktecU8yCc/HUB+H5iuonS/27GefozuIrclXXcLOLnTJ+YaFL5niZ/3Y3/GwAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAsElEQVRIie2SwQ3DIAxFf6oMkt4Ygz24NBMwQpIRmCC9sAdjcMwmzcWViFWCk6rKobwLsjG2vz7Aj2mkhdbHAcCDwqczapK8ux1oPlLYARgpV2SjwPqoAczU5BM9nXPmfgHQO6PCO9GygmGnueS+o+H33AANAM4osTcp1scXX0DkwTdwBRtooyJ7iq9VcNaLlOpBkT/2QKquelCEKwgAtPT/ZwhpwBVMvOAgC/WoyFkByGYvOegQWMwAAAAASUVORK5CYII="
ui.run(dark=True, title="Work Tool Hub", favicon=fav_icon, show_welcome_message=False)
