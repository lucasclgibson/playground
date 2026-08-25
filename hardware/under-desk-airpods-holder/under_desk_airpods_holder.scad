// ---------------------------------------------------------------------------
// Under-desk AirPods Pro case tray
//
// A shallow open-front tray that screws to the underside of a desk. The case
// lies flat, big face to the desk, and slides in and out from the front. A
// thumb notch in the floor at the mouth lets you push it back out.
//
// Lying flat is what makes this simple. Stood on end the case would have to be
// held up against gravity, which needs a snap, and a shallow socket has no
// wall length to spring with. Flat, the floor does the work and there is
// nothing to latch.
//
// Apple publishes the case as 45.2 x 60.6 x 21.7 mm but not its radii. Lying
// flat that hardly matters - a square pocket takes the case whatever its
// corners do, and the only place it shows is that the case rests on the flat
// middle of its face rather than right out at the edges, which is why the
// floor is solid rather than a pair of shelves.
//
//   x = case width, y = depth front to back, z = height, 0 = desk underside
//
// Render:  openscad -o tray.stl under_desk_airpods_holder.scad
// ---------------------------------------------------------------------------

/* [Case] Apple AirPods Pro 2 charging case, lying flat */
CASE_W = 60.6;           // left-right
CASE_D = 45.2;           // front-back once it is lying down
CASE_T = 21.7;           // thickness, which is now the depth of the tray

/* [Fit] */
GAP_SIDE = 0.4;          // snug: the case is a known size, so this can be tight
GAP_TOP  = 0.5;
GAP_BACK = 0.6;

/* [Tray] */
WALL      = 2.5;
TOP_T     = 3.0;         // the face that beds against the desk
FLOOR_T   = 2.5;         // solid: the case's face is only flat in the middle
BACK_T    = 2.5;
FRONT_LIP = 2.0;
NOTCH_W   = 24.0;        // thumb slot in the floor. Wide enough for a thumb, and
NOTCH_L   = 34.0;        // long enough to run it back behind the case and drag
                         // the case out. It costs floor: what is left either
                         // side of it is what the case actually rests on.
CHAMFER   = 1.2;         // lead-in around the mouth

/* [Mounting pads] Two, one per side, full depth. Outboard so a driver can get
   at the screws from below without reaching into the tray. */
EAR_L = 13.0;
EAR_T = 5.0;

/* [Fasteners] Two #8 or M4 flat-head wood screws */
SCREW_D    = 5.0;
HEAD_D     = 9.5;
CSK_ANGLE  = 90.0;
DRIVER_CLR = 1.5;

/* [Output] */
PRINT_ORIENTATION = true;    // laid on its back face, which is how it prints
SHOW_CASE = false;
$fn = 48;

// --------------------------- derived --------------------------------------

CAV_W = CASE_W + 2 * GAP_SIDE;
CAV_T = CASE_T + GAP_TOP;
OUT_W = CAV_W + 2 * WALL;
OUT_D = BACK_T + CASE_D + GAP_BACK + FRONT_LIP;
OUT_H = TOP_T + CAV_T + FLOOR_T;

X_CAV = CAV_W / 2;
X_OUT = OUT_W / 2;
X_EAR = X_OUT + EAR_L;
SCREW_X = X_OUT + EAR_L / 2;
SCREW_Y = OUT_D / 2;

Z_FLOOR = -(TOP_T + CAV_T);      // floor's top face = where the case rests
Z_BOT   = -OUT_H;
CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
EPS = 0.01;

assert(EAR_T > CSK_DEPTH + 1.5, "too little pad left under the countersink");
assert(SCREW_X - HEAD_D / 2 - DRIVER_CLR >= X_OUT,
       "the side wall crowds the screw heads; raise EAR_L");
assert(SCREW_X + HEAD_D / 2 < X_EAR, "the screw head overhangs the pad");
assert(NOTCH_W + 8 < CAV_W, "the thumb slot is wider than the tray");
assert((CASE_W - CASE_T - NOTCH_W) / 2 >= 4,
       "the slot leaves too little flat floor either side to rest the case on");
assert(NOTCH_L < CASE_D, "the slot runs past the back of the case");
assert(CHAMFER < WALL, "the lead-in chamfer eats the whole wall");

// --------------------------- helpers --------------------------------------

module boxc(x0, x1, y0, y1, z0, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}

// --------------------------- the part --------------------------------------

module tray() {
    difference() {
        union() {
            boxc(-X_OUT, X_OUT, 0, OUT_D, Z_FLOOR - FLOOR_T, Z_FLOOR);  // floor
            boxc(-X_OUT, X_OUT, 0, OUT_D, -TOP_T, 0);                   // top plate
            boxc(-X_OUT, X_OUT, 0, BACK_T, Z_BOT, 0);                   // back wall
            for (m = [0, 1]) mirror([m, 0, 0]) {
                boxc(X_CAV, X_OUT, 0, OUT_D, Z_BOT, 0);                 // side wall
                boxc(X_OUT, X_EAR, 0, OUT_D, -EAR_T, 0);                // mounting pad
            }
        }

        // Screws, countersunk from below.
        for (sx = [-SCREW_X, SCREW_X]) {
            translate([sx, SCREW_Y, -EAR_T - EPS])
                cylinder(h = EAR_T + 2 * EPS, d = SCREW_D);
            translate([sx, SCREW_Y, -EAR_T - EPS])
                cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);
        }

        // Thumb slot: a channel up the middle of the floor, open at the mouth,
        // so a thumb can run back along the case's underside and drag it out.
        // It opens towards the mouth and never closes again, so printed on its
        // back face there is nothing to bridge.
        hull() for (y = [OUT_D - NOTCH_L + NOTCH_W / 2, OUT_D + 1])
            translate([0, y, Z_FLOOR - FLOOR_T - EPS])
                cylinder(h = FLOOR_T + 2 * EPS, d = NOTCH_W);

        // Lead-in chamfer around the mouth.
        hull() {
            boxc(-X_CAV, X_CAV, OUT_D - CHAMFER, OUT_D - CHAMFER + EPS,
                 Z_FLOOR, -TOP_T);
            boxc(-X_CAV - CHAMFER - 1, X_CAV + CHAMFER + 1, OUT_D + 1 - EPS, OUT_D + 1,
                 Z_FLOOR - CHAMFER - 1, -TOP_T + CHAMFER + 1);
        }
    }
}

// Printed on its back face: the walls, floor and top plate all run along the
// build direction, so nothing overhangs but the countersinks.
if (PRINT_ORIENTATION) rotate([90, 0, 0]) tray();
else {
    tray();
    if (SHOW_CASE)
        %translate([-CASE_W / 2, BACK_T, Z_FLOOR]) cube([CASE_W, CASE_D, CASE_T]);
}
