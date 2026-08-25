// ---------------------------------------------------------------------------
// Under-desk power bank mount
//
// An open-front cradle that screws to the underside of a desk. The power bank
// slides in horizontally from the front and is carried by two bottom shelves,
// stopped at the back by the rear wall and held in by a pair of ramped nubs.
//
// Everything below is derived from the parameter block, so a different power bank
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

/* [Power bank] */
BANK_W = 83.0;             // left-right
BANK_D = 165.0;            // front-back, the long axis
BANK_H = 52.7;             // top-bottom

/* [Fit] */
GAP_SIDE = 0.8;          // per side
GAP_TOP  = 1.2;          // pure clearance: nothing lifts the PC
GAP_BACK = 1.0;          // front-back slack between rear wall and barbs

/* [Structure] */
WALL      = 3.0;         // side walls
TOP_T     = 3.0;         // top plate, the face that meets the desk
SHELF_T   = 4.0;         // bottom support lips
SHELF_W   = 12.0;        // how far the lips reach in from each wall
BACK_T    = 3.5;         // rear stop wall
FRONT_LIP = 10.0;        // tray depth ahead of the PC, carries the barbs

/* [Mounting pads] Four tabs rather than full-length flanges: the same screw
   pattern for a third of the material. Uniform thickness on purpose - a
   gusset at the root reaches under the screw head and fouls the driver, so
   the pad is simply thick enough not to need one. */
EAR_L      = 14.0;       // outward reach beyond the body
EAR_PAD    = 48.0;       // length of a pad where it meets the wall
EAR_END    = 21.0;       // run-out at each end; longer than EAR_L keeps the
                         // taper under 45 degrees in the build direction
EAR_T      = 6.5;        // thickness
DRIVER_CLR = 2.0;        // clear ring around each head for a bit or driver

/* [Fasteners] 4x #8 or M4 flat-head wood screws, 20-25 mm long */
SCREW_D     = 5.0;       // clearance hole, loose on a #8 or M4
HEAD_D      = 9.5;       // countersink top diameter; set = SCREW_D to disable
CSK_ANGLE   = 90.0;      // included angle
SCREW_INSET = 30.0;      // from the back and front faces

/* [Latches] Two sprung arms sweep in from the shelves to the middle of the
   mouth and stand a barb up in front of the PC. They reach the middle on
   purpose: a machine with rounded corners has no flat front face out at the
   walls, so a barb there catches nothing. The arms are the spring, they flex
   down into the open underside, and you press them to let the PC out. */
ARM_W     = 12.0;        // arm width
ARM_T     = 3.0;         // arm thickness - this is the spring
ARM_X     = 14.0;        // how far out from the centre line each barb sits
MAX_CORNER_R = 15.0;     // corner radius the barbs still land clear of. A power
                         // bank is a much squarer brick than a Mac mini, so
                         // this is generous; the check enforces it either way
ARM_ANGLE = 30.0;        // sweep from the direction of travel; shallower than
                         // the mini PC's, to buy back arm length on a narrower bay
BARB_H    = 3.0;         // how far the barb stands above the pocket floor
BARB_LEAD = 30.0;        // lead-in ramp: the PC's underside presses the arm down
BARB_HOOK = 90.0;        // retaining face: square, so nothing cams it out
BARB_FLAT = 1.0;         // flat at the crest

/* [Vents] Stretched honeycomb: hexagons with vertical flanks and pointed
   ends, the points along the build direction. A cell closes at VENT_ANGLE
   instead of bridging flat across its width, so the grid needs no bridging
   at all. */
VENT_W     = 12.0;       // cell width across the flats
VENT_LEN   = 26.0;       // cell length along the build direction
VENT_ANGLE = 60.0;       // end slope from horizontal; >= 45 prints unsupported
VENT_RIB   = 2.0;        // material left between cells
TOP_VENT_BORDER  = 8.0;  // solid margin around the top-plate field
SIDE_VENT_BORDER = 11.0; // solid margin at each end of a side wall
SIDE_VENT_MARGIN = 4.0;  // solid wall left above and below the band

REAR_W = 60.0;           // rear vent / cable pass
REAR_H = 34.0;
REAR_R = 6.0;
CHAMFER = 1.5;           // lead-in around the front opening

/* [Output] */
PRINT_ORIENTATION = false;   // true: laid on its back face, ready to slice
SHOW_BANK = false;             // preview the power bank in place
$fn = 64;

// --------------------------- derived --------------------------------------

CAV_W = BANK_W + 2 * GAP_SIDE;
CAV_H = BANK_H + GAP_TOP;
OUT_W = CAV_W + 2 * WALL;
OUT_D = BACK_T + BANK_D + GAP_BACK + FRONT_LIP;
OUT_H = TOP_T + CAV_H + max(SHELF_T, ARM_T);   // the arms hang lowest

X_OUT   = OUT_W / 2;             // outer face of the side walls
X_CAV   = CAV_W / 2;             // inner face of the side walls
X_SHELF = X_CAV - SHELF_W;       // inner edge of the shelves
X_EAR   = X_OUT + EAR_L;         // pad tip
SCREW_X = X_OUT + EAR_L / 2;

Z_CAV_TOP = -TOP_T;              // ceiling of the pocket
Z_FLOOR   = -(TOP_T + CAV_H);    // shelf top face = pocket floor
Z_BOT     = -OUT_H;              // lowest point of the part

SCREW_YS = [SCREW_INSET, OUT_D - SCREW_INSET];   // add a value for a third pair

BANK_FRONT  = BACK_T + BANK_D + GAP_BACK;            // front face, pushed forward
BARB_Y1   = BANK_FRONT + BARB_H / tan(BARB_HOOK);  // crest, back edge
BARB_Y2   = BARB_Y1 + BARB_FLAT;                 // crest, front edge
BARB_Y3   = BARB_Y2 + BARB_H / tan(BARB_LEAD);   // foot of the lead-in ramp

ARM_KNEE  = BANK_FRONT - 4;                        // where the sweep straightens
ARM_ROOT  = ARM_KNEE - (X_OUT - ARM_X) / tan(ARM_ANGLE);   // buried in the wall

VENT_RISE = VENT_W / 2 * tan(VENT_ANGLE);        // height of one pointed end
VENT_SIDE = VENT_LEN - 2 * VENT_RISE;            // length of the vertical flank

CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
EPS = 0.01;

assert(SHELF_W < X_CAV, "shelves overlap on the centre line");
assert(EAR_END > EAR_L, "pad ends would overhang steeper than 45 degrees");
assert(EAR_PAD > 2 * EAR_END, "mounting pads taper away to nothing; raise EAR_PAD");
assert(EAR_PAD - EAR_END > HEAD_D + 4, "no room for a screw head on the pad");
assert(SCREW_X - HEAD_D / 2 - DRIVER_CLR >= X_OUT,
       "the side wall crowds the screw heads; raise EAR_L");
assert(VENT_ANGLE >= 45, "vent ends would need support");
assert(VENT_SIDE > 0, "vent cells are too short for their angle; raise VENT_LEN");
assert(BARB_Y3 <= OUT_D - CHAMFER, "the barb runs into the front chamfer");
assert(ARM_X + ARM_W / 2 < X_SHELF, "the arms would foul the shelves");
assert(ARM_X + ARM_W / 2 <= BANK_W / 2 - MAX_CORNER_R,
       "the barbs reach into the corner radius; move them in");
assert(ARM_ANGLE < 45, "the arm sweep would need support");
assert(ARM_ROOT > BACK_T, "the arm root runs into the back wall; sweep it harder");

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

// One vent cell: vertical flanks with a pointed end at each side. Shrinking
// the tile by half the rib is what makes the web between cells come out an
// even VENT_RIB everywhere, corners included.
module vent_cell(w, side, rise, rib) {
    offset(delta = -rib / 2)
        polygon([[ w / 2, -side / 2], [ w / 2, side / 2], [0,  side / 2 + rise],
                 [-w / 2,  side / 2], [-w / 2, -side / 2], [0, -side / 2 - rise]]);
}

// Field of cells centred on the origin, filling u_ext x v_ext. Rows interlock
// the way a honeycomb does - the point of one cell lands in the notch between
// two of the row above - so the tiling is exact for any cell proportion. Cells
// that would hang over a border are dropped whole rather than clipped, so the
// margins never end in slivers.
module vent_field(u_ext, v_ext, w, len, angle, rib) {
    rise = w / 2 * tan(angle);
    side = len - 2 * rise;
    dv   = side + rise;              // rows overlap by one point
    nrow = floor((v_ext - len) / dv) + 1;
    kmax = ceil(u_ext / w);
    for (j = [0 : nrow - 1])
        for (k = [-kmax : kmax]) {
            cu = (j % 2) * w / 2 + k * w;
            if (abs(cu) + w / 2 <= u_ext / 2 + EPS)
                translate([cu, -(nrow - 1) * dv / 2 + j * dv])
                    vent_cell(w, side, rise, rib);
        }
}

// One mounting pad, centred on cy: a flat tab clipped to a plan trapezoid so
// both ends run out shallower than 45 degrees in the build direction.
module ear(cy) {
    y0 = cy - EAR_PAD / 2;
    y1 = cy + EAR_PAD / 2;
    intersection() {
        boxc(X_OUT, X_EAR, y0, y1, -EAR_T, 0);
        translate([0, 0, -EAR_T - 1]) linear_extrude(height = EAR_T + 2)
            polygon([[X_OUT, y0], [X_EAR, y0 + EAR_END],
                     [X_EAR, y1 - EAR_END], [X_OUT, y1]]);
    }
}

// One sprung arm in plan: swept in from the wall at ARM_ANGLE, then straight
// for the last stretch, where the barb sits. The root is buried in the wall
// and shelf, so the arm grows sideways out of supported material instead of
// starting in mid air, and the sweep stays under 45 degrees the whole way.
module arm_plan() {
    adx = ARM_X - X_OUT;
    ady = ARM_KNEE - ARM_ROOT;
    alen = sqrt(adx * adx + ady * ady);
    nx = ady / alen * ARM_W / 2;                 // normal to the sweep
    ny = -adx / alen * ARM_W / 2;
    polygon([[X_OUT + nx, ARM_ROOT + ny], [ARM_X + nx, ARM_KNEE + ny],
             [ARM_X - nx, ARM_KNEE - ny], [X_OUT - nx, ARM_ROOT - ny]]);
    translate([ARM_X - ARM_W / 2, ARM_KNEE - ARM_W])
        square([ARM_W, OUT_D - ARM_KNEE + ARM_W]);
}

// The arm sits flush with the pocket floor, so it also carries the middle of
// the PC, and hangs free underneath where it has room to flex.
module arm() {
    translate([0, 0, Z_FLOOR - ARM_T]) linear_extrude(height = ARM_T) arm_plan();
}

// Shallow ramp facing the mouth so the PC's underside presses the arm down on
// the way in; square face behind it so nothing cams the PC back out. The foot
// sinks EPS into the arm rather than sitting exactly on its top plane - that
// plane is rebuilt by (Z_FLOOR - ARM_T) + ARM_T, which is not always the same
// float as Z_FLOOR, and a union of two solids that merely touch comes apart.
module arm_barb() {
    extrude_x([[BANK_FRONT, Z_FLOOR - EPS], [BARB_Y1, Z_FLOOR + BARB_H],
               [BARB_Y2, Z_FLOOR + BARB_H], [BARB_Y3, Z_FLOOR - EPS]],
              ARM_X - ARM_W / 2, ARM_X + ARM_W / 2);
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
        // Sprung latch arm, reaching in to where the front face is flat.
        arm();
        arm_barb();
    }
}

module cuts() {
    // Screw holes, countersunk for flat-head screws.
    for (sx = [-SCREW_X, SCREW_X], sy = SCREW_YS) {
        translate([sx, sy, -EAR_T - EPS])
            cylinder(h = EAR_T + 2 * EPS, d = SCREW_D);
        if (HEAD_D > SCREW_D)
            translate([sx, sy, -EAR_T - EPS])
                cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);
    }

    // Rear cable / port cutout.
    translate([0, 0, (Z_CAV_TOP + Z_FLOOR) / 2]) hull()
        for (cx = [-1, 1] * (REAR_W / 2 - REAR_R), cz = [-1, 1] * (REAR_H / 2 - REAR_R))
            translate([cx, -EPS, cz]) rotate([-90, 0, 0])
                cylinder(h = BACK_T + 2 * EPS, r = REAR_R);

    // Top-plate vents.
    translate([0, OUT_D / 2, Z_CAV_TOP - EPS])
        linear_extrude(height = TOP_T + 2 * EPS)
            vent_field(OUT_W - 2 * TOP_VENT_BORDER, OUT_D - 2 * TOP_VENT_BORDER,
                       VENT_W, VENT_LEN, VENT_ANGLE, VENT_RIB);

    // Side-wall vents, across the band of wall that faces the PC.
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([X_CAV - EPS, OUT_D / 2, (Z_CAV_TOP + Z_FLOOR) / 2])
            rotate([0, 90, 0]) linear_extrude(height = WALL + 2 * EPS)
                vent_field(CAV_H - 2 * SIDE_VENT_MARGIN,
                           OUT_D - 2 * SIDE_VENT_BORDER,
                           VENT_W, VENT_LEN, VENT_ANGLE, VENT_RIB);

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
    if (SHOW_BANK)
        %translate([-BANK_W / 2, BACK_T, Z_FLOOR]) cube([BANK_W, BANK_D, BANK_H]);
}
