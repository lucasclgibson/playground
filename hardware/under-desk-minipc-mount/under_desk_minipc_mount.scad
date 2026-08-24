// ---------------------------------------------------------------------------
// Under-desk mini PC mount
//
// An open-front cradle that screws to the underside of a desk. The mini PC
// slides in horizontally from the front and is carried by two bottom shelves,
// stopped at the back by the rear wall and held in by a pair of ramped nubs.
//
// Everything below is derived from the parameter block, so a different mini PC
// is a three-number edit.
//
//   x = width,  0 = centre line
//   y = depth,  0 = back face, +y = towards the open front
//   z = height, 0 = desk underside (top of the flanges), -z = down
//
// Render:  openscad -o mount.stl under_desk_minipc_mount.scad
//          openscad -o mount-print.stl -D PRINT_ORIENTATION=true \
//                   under_desk_minipc_mount.scad
// ---------------------------------------------------------------------------

/* [Mini PC] */
PC_W = 129.0;            // left-right
PC_D = 129.0;            // front-back
PC_H = 45.5;             // top-bottom

/* [Fit] */
GAP_SIDE = 1.0;          // per side
GAP_TOP  = 2.0;          // must be larger than NUB_H
GAP_BACK = 1.5;          // front-back slack between rear wall and nubs

/* [Structure] */
WALL      = 3.0;         // side walls
TOP_T     = 5.0;         // top plate, the face that meets the desk
SHELF_T   = 4.0;         // bottom support lips
SHELF_W   = 12.0;        // how far the lips reach in from each wall
BACK_T    = 4.0;         // rear stop wall
FRONT_LIP = 9.5;         // tray depth ahead of the seated PC, carries the nubs

/* [Mounting flanges] */
EAR_L      = 20.0;       // outward reach beyond the body
EAR_T      = 6.0;        // thickness at the screw pads
EAR_ROOT_T = 11.0;       // thickness where it meets the wall
EAR_TAPER  = 8.0;        // length of the root gusset

/* [Fasteners] 4x #8 or M4 flat-head wood screws, 20-25 mm long */
SCREW_D     = 4.5;       // clearance hole
HEAD_D      = 9.5;       // countersink top diameter; set = SCREW_D to disable
CSK_ANGLE   = 90.0;      // included angle
SCREW_INSET = 32.0;      // from the back and front faces

/* [Retention nubs] */
NUB_H           = 1.5;
NUB_RAMP_BACK   = 2.5;   // steep side: firm pull to remove
NUB_FLAT        = 2.0;
NUB_RAMP_FRONT  = 4.0;   // shallow side: easy push to insert

/* [Vents and lightening] */
TOP_SLOTS      = 5;
TOP_SLOT_W     = 10.0;
TOP_SLOT_INSET = 12.0;
SIDE_SLOT_ZS   = [-14.0, -29.0, -44.0];
SIDE_SLOT_H    = 10.0;
SIDE_SLOT_INSET = 24.0;
PORT_W = 107.0;          // rear cable / port cutout
PORT_H = 33.0;
PORT_R = 6.0;
CHAMFER = 1.5;           // lead-in around the front opening

/* [Output] */
PRINT_ORIENTATION = false;   // true: laid on its back face, ready to slice
SHOW_PC = false;             // preview the mini PC in place
$fn = 64;

// --------------------------- derived --------------------------------------

CAV_W = PC_W + 2 * GAP_SIDE;
CAV_H = PC_H + GAP_TOP;
OUT_W = CAV_W + 2 * WALL;
OUT_D = BACK_T + PC_D + GAP_BACK + FRONT_LIP;
OUT_H = TOP_T + CAV_H + SHELF_T;

X_OUT   = OUT_W / 2;             // outer face of the side walls
X_CAV   = CAV_W / 2;             // inner face of the side walls
X_SHELF = X_CAV - SHELF_W;       // inner edge of the shelves
X_EAR   = X_OUT + EAR_L;         // flange tip
SCREW_X = X_OUT + EAR_L / 2;

Z_CAV_TOP = -TOP_T;              // ceiling of the pocket
Z_FLOOR   = -(TOP_T + CAV_H);    // shelf top face = pocket floor
Z_BOT     = -OUT_H;              // lowest point of the part

NUB_Y0 = BACK_T + PC_D + GAP_BACK;          // front face of the PC, pushed home
NUB_Y1 = NUB_Y0 + NUB_RAMP_BACK;
NUB_Y2 = NUB_Y1 + NUB_FLAT;
NUB_Y3 = NUB_Y2 + NUB_RAMP_FRONT;

CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
EPS = 0.01;

assert(GAP_TOP > NUB_H, "GAP_TOP must exceed NUB_H or the PC cannot ride in");
assert(NUB_Y3 < OUT_D, "the nub runs past the front edge; raise FRONT_LIP");
assert(SHELF_W < X_CAV, "shelves overlap on the centre line");

// --------------------------- helpers --------------------------------------

// Axis-aligned box from two opposite corners.
module boxc(x0, x1, y0, y1, z0, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}

// Convex (x,z) profile swept along y.
module extrude_y(profile, y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0])
        linear_extrude(height = y1 - y0) polygon(profile);
}

// Convex (y,z) profile swept along x.
module extrude_x(profile, x0, x1) {
    translate([x0, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 90])
        linear_extrude(height = x1 - x0) polygon(profile);
}

// Slot with semicircular ends, swept along y, rounded across x/z.
module slot_z(cx, y0, y1, w, z0, z1) {          // through the top plate
    hull() for (cy = [y0 + w / 2, y1 - w / 2])
        translate([cx, cy, z0]) cylinder(h = z1 - z0, d = w);
}

module slot_x(cz, y0, y1, h, x0, x1) {          // through a side wall
    hull() for (cy = [y0 + h / 2, y1 - h / 2])
        translate([x0, cy, cz]) rotate([0, 90, 0]) cylinder(h = x1 - x0, d = h);
}

// --------------------------- the part --------------------------------------

module body() {
    // Top plate: the face that beds against the desk.
    boxc(-X_OUT, X_OUT, 0, OUT_D, Z_CAV_TOP, 0);
    // Rear stop wall.
    boxc(-X_OUT, X_OUT, 0, BACK_T, Z_BOT, 0);

    for (m = [0, 1]) mirror([m, 0, 0]) {
        // Side wall, full height and full depth.
        boxc(X_CAV, X_OUT, 0, OUT_D, Z_BOT, 0);
        // Bottom shelf the PC rests on.
        boxc(X_SHELF, X_CAV, 0, OUT_D, Z_BOT, Z_FLOOR);
        // Mounting flange: flat screw pad plus a tapered gusset at the root.
        boxc(X_OUT, X_EAR, 0, OUT_D, -EAR_T, 0);
        extrude_y([[X_OUT, -EAR_ROOT_T], [X_OUT, -EAR_T],
                   [X_OUT + EAR_TAPER, -EAR_T]], 0, OUT_D);
        // Retention nub: shallow ramp in, steep ramp out.
        extrude_x([[NUB_Y0, Z_FLOOR], [NUB_Y1, Z_FLOOR + NUB_H],
                   [NUB_Y2, Z_FLOOR + NUB_H], [NUB_Y3, Z_FLOOR]],
                  X_SHELF, X_CAV);
    }
}

module cuts() {
    // Screw holes, countersunk for flat-head screws.
    for (sx = [-SCREW_X, SCREW_X], sy = [SCREW_INSET, OUT_D - SCREW_INSET]) {
        translate([sx, sy, -EAR_ROOT_T - EPS])
            cylinder(h = EAR_ROOT_T + 2 * EPS, d = SCREW_D);
        if (HEAD_D > SCREW_D)
            translate([sx, sy, -EAR_T - EPS])
                cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);
    }

    // Rear cable / port cutout.
    translate([0, 0, (Z_CAV_TOP + Z_FLOOR) / 2]) hull()
        for (cx = [-1, 1] * (PORT_W / 2 - PORT_R), cz = [-1, 1] * (PORT_H / 2 - PORT_R))
            translate([cx, -EPS, cz]) rotate([-90, 0, 0])
                cylinder(h = BACK_T + 2 * EPS, r = PORT_R);

    // Top-plate slots. Long in y, so every bridge is only TOP_SLOT_W wide.
    pitch = (CAV_W - 2 * TOP_SLOT_INSET) / (TOP_SLOTS - 1);
    for (i = [0 : TOP_SLOTS - 1])
        slot_z(-(X_CAV - TOP_SLOT_INSET) + i * pitch,
               TOP_SLOT_INSET, OUT_D - TOP_SLOT_INSET, TOP_SLOT_W,
               Z_CAV_TOP - EPS, EPS);

    // Side-wall vents, likewise long in y.
    for (cz = SIDE_SLOT_ZS, m = [0, 1]) mirror([m, 0, 0])
        slot_x(cz, SIDE_SLOT_INSET, OUT_D - SIDE_SLOT_INSET, SIDE_SLOT_H,
               X_CAV - EPS, X_OUT + EPS);

    // Lead-in chamfer around the front opening (walls and ceiling, not the
    // shelves - the nubs live there).
    grow = CHAMFER + 1;
    hull() {
        boxc(-X_CAV, X_CAV, OUT_D - CHAMFER, OUT_D - CHAMFER + EPS, Z_FLOOR, Z_CAV_TOP);
        boxc(-X_CAV - grow, X_CAV + grow, OUT_D + 1 - EPS, OUT_D + 1,
             Z_FLOOR, Z_CAV_TOP + grow);
    }
}

module mount() {
    difference() {
        body();
        cuts();
    }
}

if (PRINT_ORIENTATION) {
    // Rolled onto its back face: flat on the bed, nothing needs support.
    rotate([90, 0, 0]) mount();
} else {
    mount();
    if (SHOW_PC)
        %translate([-PC_W / 2, BACK_T, Z_FLOOR]) cube([PC_W, PC_D, PC_H]);
}
