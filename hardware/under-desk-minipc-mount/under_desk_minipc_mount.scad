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
//   z = height, 0 = desk underside (top of the plate and pads), -z = down
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
TOP_T     = 3.0;         // top plate, the face that meets the desk
SHELF_T   = 4.0;         // bottom support lips
SHELF_W   = 12.0;        // how far the lips reach in from each wall
BACK_T    = 3.5;         // rear stop wall
FRONT_LIP = 8.0;         // tray depth ahead of the seated PC, carries the nubs

/* [Mounting pads] Four tabs rather than full-length flanges: the same screw
   pattern for a third of the material. The ends taper at 45 degrees so they
   still print without support. */
EAR_L      = 14.0;       // outward reach beyond the body
EAR_PAD    = 48.0;       // length of a pad where it meets the wall
EAR_END    = 21.0;       // run-out at each end; longer than EAR_L keeps the
                         // taper under 45 degrees in the build direction
EAR_T      = 5.0;        // thickness at the screw
EAR_ROOT_T = 9.0;        // thickness where it meets the wall
EAR_TAPER  = 6.0;        // length of the root gusset

/* [Fasteners] 4x #8 or M4 flat-head wood screws, 20-25 mm long */
SCREW_D     = 4.5;       // clearance hole
HEAD_D      = 9.5;       // countersink top diameter; set = SCREW_D to disable
CSK_ANGLE   = 90.0;      // included angle
SCREW_INSET = 30.0;      // from the back and front faces

/* [Retention nubs] */
NUB_H           = 1.5;
NUB_RAMP_BACK   = 2.5;   // steep side: firm pull to remove
NUB_FLAT        = 1.5;
NUB_RAMP_FRONT  = 3.5;   // shallow side: easy push to insert

/* [Vents] Honeycomb. Cells sit flat-side-up in the build direction, so each
   one closes with a short bridge the width of a single hexagon side rather
   than the 30 degree overhang a point-up cell would give. */
VENT_AF  = 14.0;         // hexagon across the flats
VENT_RIB = 2.5;          // material left between cells
TOP_VENT_BORDER  = 8.0;  // solid margin around the top-plate field
SIDE_VENT_BORDER = 12.0; // solid margin at each end of a side wall
SIDE_VENT_MARGIN = 4.0;  // solid wall left above and below the band

PORT_W = 113.0;          // rear cable / port cutout
PORT_H = 37.0;
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
X_EAR   = X_OUT + EAR_L;         // pad tip
SCREW_X = X_OUT + EAR_L / 2;

Z_CAV_TOP = -TOP_T;              // ceiling of the pocket
Z_FLOOR   = -(TOP_T + CAV_H);    // shelf top face = pocket floor
Z_BOT     = -OUT_H;              // lowest point of the part

SCREW_YS = [SCREW_INSET, OUT_D - SCREW_INSET];   // add a value for a third pair

NUB_Y0 = BACK_T + PC_D + GAP_BACK;          // front face of the PC, pushed home
NUB_Y1 = NUB_Y0 + NUB_RAMP_BACK;
NUB_Y2 = NUB_Y1 + NUB_FLAT;
NUB_Y3 = NUB_Y2 + NUB_RAMP_FRONT;

CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
EPS = 0.01;

assert(GAP_TOP > NUB_H, "GAP_TOP must exceed NUB_H or the PC cannot ride in");
assert(NUB_Y3 < OUT_D, "the nub runs past the front edge; raise FRONT_LIP");
assert(SHELF_W < X_CAV, "shelves overlap on the centre line");
assert(EAR_END > EAR_L, "pad ends would overhang steeper than 45 degrees");
assert(EAR_PAD > 2 * EAR_END, "mounting pads taper away to nothing; raise EAR_PAD");
assert(EAR_PAD - EAR_END > HEAD_D + 4, "no room for a screw head on the pad");

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

// Honeycomb field, centred on the origin and filling u_ext x v_ext. Cells are
// pointed across u and flat across v, so with v along the build direction the
// only overhang in the whole grid is the flat top of each cell - one hexagon
// side wide. Columns that would hang over the edge of the field are dropped
// rather than clipped, so the border never ends in slivers.
module honeycomb(u_ext, v_ext, af, rib) {
    pitch = af + rib;                // centre-to-centre, any direction
    du = pitch * sqrt(3) / 2;        // column pitch
    r  = af / sqrt(3);               // circumradius of one cell
    ncol = floor((u_ext - 2 * r) / du) + 1;
    nrow = floor((v_ext - af) / pitch) + 1;
    for (i = [0 : ncol - 1]) {
        n = nrow - (i % 2);          // staggered columns hold one cell fewer
        for (j = [0 : n - 1])
            translate([-(ncol - 1) * du / 2 + i * du,
                       -(n - 1) * pitch / 2 + j * pitch])
                circle(r = r, $fn = 6);
    }
}

// One mounting pad, centred on cy: a flat screw pad with a gusset underneath,
// clipped to a plan trapezoid so both ends run out at 45 degrees.
module ear(cy) {
    y0 = cy - EAR_PAD / 2;
    y1 = cy + EAR_PAD / 2;
    intersection() {
        union() {
            boxc(X_OUT, X_EAR, y0, y1, -EAR_T, 0);
            extrude_y([[X_OUT, -EAR_ROOT_T], [X_OUT, -EAR_T],
                       [X_OUT + EAR_TAPER, -EAR_T]], y0, y1);
        }
        translate([0, 0, -EAR_ROOT_T - 1])
            linear_extrude(height = EAR_ROOT_T + 2)
                polygon([[X_OUT, y0], [X_EAR, y0 + EAR_END],
                         [X_EAR, y1 - EAR_END], [X_OUT, y1]]);
    }
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
        // Mounting pads.
        for (cy = SCREW_YS) ear(cy);
        // Retention nub: shallow ramp in, steep ramp out.
        extrude_x([[NUB_Y0, Z_FLOOR], [NUB_Y1, Z_FLOOR + NUB_H],
                   [NUB_Y2, Z_FLOOR + NUB_H], [NUB_Y3, Z_FLOOR]],
                  X_SHELF, X_CAV);
    }
}

module cuts() {
    // Screw holes, countersunk for flat-head screws.
    for (sx = [-SCREW_X, SCREW_X], sy = SCREW_YS) {
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

    // Top-plate honeycomb.
    translate([0, OUT_D / 2, Z_CAV_TOP - EPS])
        linear_extrude(height = TOP_T + 2 * EPS)
            honeycomb(OUT_W - 2 * TOP_VENT_BORDER, OUT_D - 2 * TOP_VENT_BORDER,
                      VENT_AF, VENT_RIB);

    // Side-wall honeycomb, across the band of wall that faces the PC.
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([X_CAV - EPS, OUT_D / 2, (Z_CAV_TOP + Z_FLOOR) / 2])
            rotate([0, 90, 0]) linear_extrude(height = WALL + 2 * EPS)
                honeycomb(CAV_H - 2 * SIDE_VENT_MARGIN,
                          OUT_D - 2 * SIDE_VENT_BORDER, VENT_AF, VENT_RIB);

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
