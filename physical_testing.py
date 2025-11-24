# Happy Holidays! This is the Opentrons Tough Cookie Maker Protocol
# This protocol is meant to be paired with the Opentrons Tough Cookie labware definition
from opentrons import protocol_api
from opentrons.protocol_api import Labware
from opentrons.types import Point, Location
from typing import List
from pydantic import BaseModel
import math

metadata = {
    "protocolName": "Opentrons Tough Cookie hardware-testing Protocol",
    "author": "Casey Batten",
}

requirements = {
    "apiLevel": "2.27",
    "robotType": "Flex",

}

# Amount of uL of frosting to dispense per mm
# This totals out to 1000~ uL of frosting for a single left-to-right line across the cookie
# So at a 1 tip for a full line, you could do 85 straight lines top to bottom with a single tiprack
FROSTING_PER_MM = 7.8

FROSTING_FLOW_RATE=100

DISPENSE_HEIGHT_ABOVE_COOKIE = 10
WAYPOINT_Z_HEIGHT = 10.0

# Known frosting colors

class CookiePoint(BaseModel):
    line_id: int
    color: str
    x: float
    y: float



def run(protocol: protocol_api.ProtocolContext):
    # Retrieve Run Time

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
    white_frosting_container = frosting_lw.well("A2")
    frosting_lw.load_liquid(["A2"], 45000, white_frosting)
    white_tip = tips["A1"]
    pipette.pick_up_tip(white_tip)
    pipette.require_liquid_presence(white_frosting_container)
    pipette.return_tip()
    #Get cookie Height

    pipette.pick_up_tip(tips["B1"])
    pipette.measure_liquid_height(cookie.well("A1"))
    pipette.return_tip()

    if protocol.is_simulating():
        well_z = 1
    else:
        well_z = cookie.well("A1").current_liquid_height()
    points = [(Point(x=-62, y = -38 + i*9, z=DISPENSE_HEIGHT_ABOVE_COOKIE-i+well_z), Point(x=62, y = -38 + i*9, z=DISPENSE_HEIGHT_ABOVE_COOKIE-i+well_z)) for i in range (8)]

    pipette.pick_up_tip(tips["A1"])
    for start, end in points:
        dist = math.sqrt(((start.x - end.x) ** 2) + ((start.y - end.y) ** 2))
        frosting_volume = FROSTING_PER_MM * dist if (FROSTING_PER_MM * dist) <= 1000 else 1000
        if pipette.current_volume < frosting_volume:
            pipette.aspirate(
                volume=1000-pipette.current_volume,
                flow_rate=FROSTING_FLOW_RATE,
                location=white_frosting_container.meniscus(z=-1, target="start"),
                end_location=white_frosting_container.meniscus(z=-1, target="end")
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

