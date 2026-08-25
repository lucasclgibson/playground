// ---------------------------------------------------------------------------
// Under-desk AirPods Pro case holder
//
// A socket that screws to the underside of a desk. Push the case up into it,
// pull it down to take it out. One screw, straight up through the ceiling of
// the socket - you drive it through the open mouth before the case goes in, so
// there is no flange hanging off the side.
//
// Apple publishes the case as 45.2 x 60.6 x 21.7 mm but not its radii. The
// ends look semicircular, which for a 21.7 mm depth means r = 10.85 - the most
// rounded that bounding box can be. A pocket cut to that only fits if the case
// really is a perfect stadium; anything squarer is wider at the corners and
// jams. So the pocket is cut to 8 mm: smaller than any plausible case radius,
// which means it takes the case either way, and the slack at the corners is
// invisible once it is in.
//
//   x = case width,  y = case thickness,  z = height, 0 = desk underside
//
// Render:  openscad -o holder.stl under_desk_airpods_holder.scad
// ---------------------------------------------------------------------------

/* [Case] Apple AirPods Pro 2 charging case */
CASE_W = 60.6;
CASE_T = 21.7;
CASE_H = 45.2;

/* [Fit] */
GAP      = 0.6;          // clearance around the case, per side
POCKET_R = 8.0;          // pocket corner radius - deliberately under the case's
DEPTH    = 30.0;         // how much of the case the socket swallows

/* [Shell] */
WALL  = 2.5;
TOP_T = 5.0;             // ceiling, thick enough to countersink into

/* [Grip] A sprung tongue in the front wall, so the hold does not depend on
   hitting a friction fit dead on. */
TONGUE_W = 14.0;
TONGUE_L = 28.0;         // from the mouth back towards the ceiling
SLOT     = 1.6;          // gap freeing it either side
BUMP     = 1.2;          // how far it stands into the pocket
BUMP_RAMP = 30.0;        // both faces, so it prints and releases either way
BUMP_FLAT = 2.0;
BUMP_Z    = 8.0;         // crest, measured up from the mouth

/* [Fastener] One #8 or M4 flat-head wood screw */
SCREW_D   = 5.0;
HEAD_D    = 9.5;
CSK_ANGLE = 90.0;

/* [Output] */
PRINT_ORIENTATION = true;    // ceiling down, which is how it prints
SHOW_CASE = false;
$fn = 64;

// --------------------------- derived --------------------------------------

POCK_W = CASE_W + 2 * GAP;
POCK_T = CASE_T + 2 * GAP;
H      = TOP_T + DEPTH;          // total drop below the desk
Z_CEIL = -TOP_T;                 // underside of the ceiling
Z_MOUTH = -H;
CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
BUMP_RUN = BUMP / tan(BUMP_RAMP);
EPS = 0.01;

assert(POCKET_R < POCK_T / 2, "pocket radius is larger than the pocket is deep");
assert(POCKET_R <= CASE_T / 2 - 1.0,
       "pocket radius leaves no margin against the case's own radius");
assert(TOP_T > CSK_DEPTH + 1.5, "too little ceiling left under the countersink");
assert(HEAD_D + 4 < POCK_T, "screw head does not fit inside the socket");
assert(TONGUE_L < DEPTH, "the tongue slot would cut into the ceiling");
assert(BUMP_Z + BUMP_RUN + BUMP_FLAT / 2 < TONGUE_L, "the bump is past the tongue");

// --------------------------- helpers --------------------------------------

// Rounded rectangle, centred.
module rrect(w, t, r) {
    offset(r = r) square([w - 2 * r, t - 2 * r], center = true);
}

// Convex (y,z) profile swept along x.
module extrude_x(profile, x0, x1) {
    translate([x0, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 90])
        linear_extrude(height = x1 - x0) polygon(profile);
}

// --------------------------- the part --------------------------------------

module holder() {
    difference() {
        // Shell: the pocket grown by the wall thickness, which rounds the
        // outside to match.
        translate([0, 0, -H]) linear_extrude(height = H)
            offset(r = WALL) rrect(POCK_W, POCK_T, POCKET_R);

        // The pocket, open at the bottom.
        translate([0, 0, -H - 1]) linear_extrude(height = H - TOP_T + 1)
            rrect(POCK_W, POCK_T, POCKET_R);

        // Screw, countersunk into the ceiling from inside the socket. Printed
        // ceiling-down this cone opens upward, so it needs no support.
        translate([0, 0, Z_CEIL - EPS]) cylinder(h = TOP_T + 2 * EPS, d = SCREW_D);
        translate([0, 0, Z_CEIL - EPS])
            cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);

        // Slots freeing the tongue. They run out of the mouth, so they open at
        // the top of the print rather than closing over a bridge.
        for (s = [-1, 1])
            translate([s * (TONGUE_W + SLOT) / 2 - SLOT / 2, POCK_T / 2 - EPS,
                       Z_MOUTH - EPS])
                cube([SLOT, WALL + 2 * EPS, TONGUE_L + EPS]);
    }

    // The bump, on the inside of the tongue. Symmetric ramps: the lower one
    // lets the case in, the upper one is what the print has to hold up, and at
    // 30 degrees off the wall neither needs support.
    // (y, z) profile. The base sits EPS inside the wall rather than exactly on
    // its face: two solids that merely touch do not always come out of a union
    // as one body.
    extrude_x([[POCK_T / 2 + EPS, Z_MOUTH + BUMP_Z - BUMP_RUN - BUMP_FLAT / 2],
               [POCK_T / 2 - BUMP, Z_MOUTH + BUMP_Z - BUMP_FLAT / 2],
               [POCK_T / 2 - BUMP, Z_MOUTH + BUMP_Z + BUMP_FLAT / 2],
               [POCK_T / 2 + EPS, Z_MOUTH + BUMP_Z + BUMP_RUN + BUMP_FLAT / 2]],
              -TONGUE_W / 2, TONGUE_W / 2);
}

// Printed ceiling-down: the desk face is the first layer, the walls rise, the
// mouth is the open top, and the countersink opens upward. Nothing overhangs.
if (PRINT_ORIENTATION) rotate([180, 0, 0]) holder();
else holder();

if (SHOW_CASE && !PRINT_ORIENTATION)
    %translate([0, 0, Z_CEIL - CASE_H])
        linear_extrude(height = CASE_H) rrect(CASE_W, CASE_T, CASE_T / 2);
