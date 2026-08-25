// ---------------------------------------------------------------------------
// Under-desk keyboard rails
//
// A channel that screws to the underside of a desk. Print two - one as it
// stands, one mirrored - screw them up the width of your keyboard apart, and
// the keyboard slides in from the front and hangs out of the way.
//
// One screw each on purpose: the spacing is yours to set when you mark the
// holes, so the same part fits any width of keyboard.
//
//   x = across, 0 = the face the keyboard's edge runs against, +x outboard
//   y = along the rail, 0 = back
//   z = height, 0 = desk underside, -z = down
//
// Render:  openscad -o right.stl under_desk_keyboard_rail.scad
//          openscad -o left.stl -D MIRROR=true under_desk_keyboard_rail.scad
// ---------------------------------------------------------------------------

/* [Keyboard] */
KB_H = 9.0;              // height at its thickest point
KB_D = 103.0;            // front to back

/* [Fit] */
GAP_H = 1.0;             // clearance above the keyboard
GAP_W = 1.5;             // total side slack, split between the two rails

/* [Rail] */
RAIL_L = 100.0;          // length; a little under the keyboard depth
LIP_IN = 9.0;            // how far the lip reaches under the keyboard
LIP_T  = 3.0;            // lip thickness
WALL   = 3.0;            // side wall
PAD_W  = 13.0;           // mounting pad, outboard of the wall
PAD_T  = 5.0;            // pad thickness
GUSSET = 8.0;            // 45 degree gusset carrying the pad
WINDOW = 15.0;           // gap in the gusset at the screw, so a driver fits
STOP_T = 3.0;            // rear stop, so the keyboard lands in the same place
LEAD   = 8.0;            // lead-in ramp at the mouth
LEAD_D = 1.5;

/* [Fastener] One #8 or M4 flat-head wood screw per rail */
SCREW_D   = 5.0;         // clearance hole
HEAD_D    = 9.5;         // countersink top diameter
CSK_ANGLE = 90.0;

/* [Output] */
MIRROR = false;              // true for the left-hand rail
SHOW_KB = false;             // preview the keyboard edge in place
$fn = 48;

// --------------------------- derived --------------------------------------

CH_H  = KB_H + GAP_H;            // channel height
H     = CH_H + LIP_T;            // total drop below the desk
Z_LIP = -CH_H;                   // the face the keyboard rests on
Z_BOT = -H;
PAD_X = WALL + PAD_W;            // outer edge of the pad
SCREW_X = WALL + PAD_W / 2;
CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
OVERHANG = PAD_W - GUSSET;       // strip of pad underside the gusset misses
EPS = 0.01;

assert(GUSSET == H - PAD_T, "the gusset is not a 45 degree run to the wall foot");
assert(WINDOW > HEAD_D + 4, "no room to get a driver into the gusset window");
assert(PAD_T > CSK_DEPTH + 1.5, "too little pad left under the countersink");
assert(SCREW_X - HEAD_D / 2 > WALL, "the screw head overhangs the wall");
assert(SCREW_X + HEAD_D / 2 < PAD_X, "the screw head overhangs the pad");
assert(RAIL_L < KB_D, "rail is longer than the keyboard is deep");

// --------------------------- helpers --------------------------------------

module boxc(x0, x1, y0, y1, z0, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}

// Convex (y,z) profile swept along x.
module extrude_x(profile, x0, x1) {
    translate([x0, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 90])
        linear_extrude(height = x1 - x0) polygon(profile);
}

// --------------------------- the part --------------------------------------

// Section through the rail: lip, wall, pad, and a gusset under the pad. The
// whole rail is this swept along its length, which is why there is nothing to
// it. The channel corner is left square - a fillet there would print nicely
// but it sits exactly where the keyboard's bottom edge wants to be.
module section() {
    polygon([[-LIP_IN, Z_BOT], [-LIP_IN, Z_LIP], [0, Z_LIP], [0, 0],
             [PAD_X, 0], [PAD_X, -PAD_T], [WALL + GUSSET, -PAD_T],
             [WALL, Z_BOT]]);
}

module rail() {
    difference() {
        union() {
            translate([0, RAIL_L, 0]) rotate([90, 0, 0])
                linear_extrude(height = RAIL_L) section();
            // Rear stop: push the keyboard in until it touches.
            boxc(-LIP_IN, WALL, 0, STOP_T, Z_LIP, 0);
        }
        // Screw, countersunk from below. Printed pad-down this cone opens
        // upward, so it needs no support and seats a flat head square.
        translate([SCREW_X, RAIL_L / 2, -PAD_T - EPS]) {
            cylinder(h = PAD_T + 2 * EPS, d = SCREW_D);
            cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);
        }
        // Gap in the gusset at the screw. The pad bridges it in about 15 mm,
        // which prints; a gusset running under the head would not let a
        // driver anywhere near it.
        boxc(WALL - EPS, WALL + GUSSET + EPS,
             RAIL_L / 2 - WINDOW / 2, RAIL_L / 2 + WINDOW / 2,
             Z_BOT - EPS, -PAD_T);
        // Lead-in at the mouth, so the keyboard finds the channel. It stops
        // dead on the wall face: overshooting into the wall leaves a sliver of
        // material hanging off it at rest-face height.
        extrude_x([[RAIL_L - LEAD, Z_LIP + EPS], [RAIL_L + 1, Z_LIP + EPS],
                   [RAIL_L + 1, Z_LIP - LEAD_D]], -LIP_IN - 1, 0);
    }
}

// It prints the way it hangs, just set down on the bed: the lip's underside is
// the first layer, the keyboard's rest face and the wall come out clean, and
// the only overhang is the strip of pad underside past the gusset.
module printable() {
    translate([0, 0, H]) rail();
}

mirror([MIRROR ? 1 : 0, 0, 0]) {
    printable();
    if (SHOW_KB)
        %translate([-60, STOP_T, Z_LIP]) cube([60, KB_D, KB_H]);
}
