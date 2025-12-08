# This protocol is meant to be paired with the Opentrons Tough Cookie labware definition
from opentrons import protocol_api
from opentrons.protocol_api import Labware
from opentrons.types import Point, Location
from typing import List
from pydantic import BaseModel
import math

metadata = {
    "protocolName": "Opentrons Tough Cookie hardware-testing Protocol",
    "author": "Ryan Howard",
}

requirements = {
    "apiLevel": "2.27",
    "robotType": "Flex",

}


WAYPOINT_Z_HEIGHT = 10.0

def add_parameters(parameters) -> None:
    """Build the runtime parameters."""
    parameters.add_int(
        display_name="Flow rate",
        variable_name="flow_rate",
        default=400,
        minimum=1,
        maximum=1000,
        description="Flow rate",
    )
    parameters.add_int(
        display_name="Drop Height",
        variable_name="drop_height",
        default=2,
        minimum=1,
        maximum=10,
        description="drop height",
    )
    parameters.add_int(
        display_name="Row Number",
        variable_name="row_num",
        default=1,
        minimum=1,
        maximum=8,
        description="Which row to use",
    )
    parameters.add_float(
        display_name="Frosting per mm",
        variable_name="frosting_per_mm",
        default=7.8,
        minimum=0.5,
        maximum=100,
        description="how much frosting to dispense per mm",
    )
    parameters.add_int(
        display_name="Pre wet cycles",
        variable_name="prewet",
        default=0,
        minimum=0,
        maximum=10,
        description="How mnay cycles to prewet the tips",
    )
    parameters.add_int(
        display_name="submerge depth",
        variable_name="submerge_depth",
        default=1,
        minimum=1,
        maximum=10,
        description="how far down the frosting container to go",
    )
    parameters.add_str(
        display_name="Frosting Well",
        variable_name="frosting_well",
        default="A2",
        choices=[
            {"display_name": name, "value": name}
            for name in [
                "A1",
                "A2",
                "A3",
                "B1",
                "B2",
                "B3",
            ]
        ],
        description="how far down the frosting container to go",
    )




def run(protocol: protocol_api.ProtocolContext):
    # Retrieve Run Time

    FROSTING_FLOW_RATE=protocol.params.flow_rate
    DISPENSE_HEIGHT_ABOVE_COOKIE = protocol.params.drop_height
    FROSTING_PER_MM=protocol.params.frosting_per_mm
    sd=-1*protocol.params.submerge_depth
    i = protocol.params.row_num
    # Load frosting tips and pipette
    tips = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "A2")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tips])

    # Load cookie
    # TODO: make the cookie definition
    cookie = protocol.load_labware("opentrons_tough_cookie", "C2")

    # Load cookie dispenser and tip trash
    #cookie_chute = protocol.load_waste_chute()
    tip_trash = protocol.load_trash_bin("A3")

    frosting_lw = protocol.load_labware(f"opentrons_6_tuberack_nest_50ml_conical", "B2")

    # Frosting declarations
    # White
    white_frosting = protocol.define_liquid("white_frosting", "White Frosting", "#FFFFFF")
    white_frosting_container = frosting_lw.well(protocol.params.frosting_well)
    frosting_lw.load_liquid(["A2"], 45000, white_frosting)
    white_tip = tips["A1"]
    pipette.pick_up_tip(white_tip)
    pipette.measure_liquid_height(cookie.well("A1"))
    pipette.require_liquid_presence(white_frosting_container)
    #Get cookie Height


    if protocol.is_simulating():
        well_z = 1
    else:
        well_z = cookie.well("A1").current_liquid_height()
    points = [(Point(x=-62, y = -38 + i*9, z=DISPENSE_HEIGHT_ABOVE_COOKIE+well_z), Point(x=62, y = -38 + i*9, z=DISPENSE_HEIGHT_ABOVE_COOKIE+well_z))]
    first_fill = True
    for start, end in points:
        dist = math.sqrt(((start.x - end.x) ** 2) + ((start.y - end.y) ** 2))
        frosting_volume = FROSTING_PER_MM * dist if (FROSTING_PER_MM * dist) <= 1000 else 1000
        if pipette.current_volume < frosting_volume:
            pipette.aspirate(
                volume=1000-pipette.current_volume,
                flow_rate=FROSTING_FLOW_RATE,
                location=white_frosting_container.meniscus(z=sd, target="start"),
                end_location=white_frosting_container.meniscus(z=sd, target="end")
            )
            if first_fill:
                first_fill = False
                for i in range(protocol.params.prewet):
                    pipette.dispense(
                        volume=1000,
                        flow_rate=FROSTING_FLOW_RATE,
                        location=white_frosting_container.meniscus(z=sd, target="start"),
                        end_location=white_frosting_container.meniscus(z=sd, target="end")
                    )
                    pipette.aspirate(
                        volume=1000,
                        flow_rate=FROSTING_FLOW_RATE,
                        location=white_frosting_container.meniscus(z=sd, target="start"),
                        end_location=white_frosting_container.meniscus(z=sd, target="end")
                    )

        start_loc = cookie["A1"].bottom().move(start)
        end_loc = cookie["A1"].bottom().move(end)
        # Move at Z height to the next start point
        pipette.move_to(start_loc.move(Point(x=0,y=0,z=WAYPOINT_Z_HEIGHT)))
        pipette.dispense(
            frosting_volume,
            flow_rate=FROSTING_FLOW_RATE,
            location=start_loc,
            end_location=end_loc
        )
        # Retract back up so we're above the frosting for the next line
        pipette.move_to(end_loc.move(Point(x=0,y=0,z=WAYPOINT_Z_HEIGHT)))
    pipette.drop_tip(tip_trash)

