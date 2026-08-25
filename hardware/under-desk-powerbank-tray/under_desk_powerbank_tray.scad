// ---------------------------------------------------------------------------
// Under-desk power bank mount
//
// An open-front cradle that screws to the underside of a desk. The power bank
// slides in horizontally from the front and is carried by two bottom shelves,
// stopped at the back by the rear wall. Nothing latches it: it is a heavy brick
// lying in a horizontal tray, so it goes in and out from the front and that is
// the whole interaction.
//
// Everything below is derived from the parameter block, so a different power bank
// is a three-number edit.
//
//   x = width,  0 = centre line
//   y = depth,  0 = back face, +y = towards the open front
//   z = height, 0 = desk underside (top of the plate and pads), -z = down
//
// Render:  openscad -o mount.stl under_desk_powerbank_tray.scad
//          openscad -o mount-print.stl -D PRINT_ORIENTATION=true \
//                   under_desk_powerbank_tray.scad
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
FRONT_LIP = 3.0;         // small margin ahead of the bank, for the chamfer

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

/* [Side band] The brick carries a raised band on one side: 18 mm across its
   52.7 mm face, running 32 mm down from the top. Laid flat, that band ends up
   on a side wall running back from the mouth, so the wall is slotted right
   through to let it pass. BAND_DEPTH is measured on the brick, not on the
   print - the slot has to run further than 32 mm because the brick's top face
   sits FRONT_LIP + GAP_BACK behind the mouth. */
BAND_SIDE  = 1;          // +1 = left as you face the open end, -1 = right
BAND_W     = 18.0;       // band width, across the 52.7 mm face
BAND_DEPTH = 32.0;       // how far it reaches down from the top of the brick
BAND_OFF   = 0.0;        // band centre off the middle of the brick's thickness
BAND_CLR   = 0.6;        // slack around the band, per side

/* [Fasteners] 4x #8 or M4 flat-head wood screws, 20-25 mm long */
SCREW_D     = 5.0;       // clearance hole, loose on a #8 or M4
HEAD_D      = 9.5;       // countersink top diameter; set = SCREW_D to disable
CSK_ANGLE   = 90.0;      // included angle
SCREW_INSET = 30.0;      // from the back and front faces

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

BANK_FRONT = BACK_T + BANK_D + GAP_BACK;         // front face, pushed forward

VENT_RISE = VENT_W / 2 * tan(VENT_ANGLE);        // height of one pointed end
VENT_SIDE = VENT_LEN - 2 * VENT_RISE;            // length of the vertical flank

// Band slot. Centred on the brick's thickness, not on the pocket's: the brick
// sits on the shelf, so that is the datum the band is measured from.
BAND_Z  = Z_FLOOR + BANK_H / 2 + BAND_OFF;
BAND_Z0 = BAND_Z - BAND_W / 2 - BAND_CLR;
BAND_Z1 = BAND_Z + BAND_W / 2 + BAND_CLR;
BAND_Y0 = BANK_FRONT - BAND_DEPTH - BAND_CLR;    // back end of the slot

// Vent field extents. The banded wall has to stop clear of the slot, so the two
// side walls carry fields of different length.
SIDE_VENT_Y0 = SIDE_VENT_BORDER;
PLAIN_VENT_Y1 = OUT_D - SIDE_VENT_BORDER;
BAND_VENT_Y1  = BAND_Y0 - VENT_RIB;

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
assert(BANK_FRONT + CHAMFER <= OUT_D, "no room for the front chamfer");
assert(BAND_Z0 > Z_FLOOR, "band slot would break into the shelf; check BAND_OFF");
assert(BAND_Z1 < Z_CAV_TOP, "band slot would break into the top plate; check BAND_OFF");
assert(BAND_VENT_Y1 - SIDE_VENT_Y0 > VENT_LEN,
       "the band slot leaves no room for vents in that wall");

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

// One side wall's vent field, spanning y0..y1, cut right through the wall.
module side_vents(y0, y1) {
    translate([X_CAV - EPS, (y0 + y1) / 2, (Z_CAV_TOP + Z_FLOOR) / 2])
        rotate([0, 90, 0]) linear_extrude(height = WALL + 2 * EPS)
            vent_field(CAV_H - 2 * SIDE_VENT_MARGIN, y1 - y0,
                       VENT_W, VENT_LEN, VENT_ANGLE, VENT_RIB);
}

// The slot the brick's side band passes through. Cut clean through the wall:
// the band stands proud of the brick by an unknown amount, so leaving any wall
// outboard of it would just be a guess. Open at the mouth, so it is a notch in
// the front opening rather than a hole - the wall closes again behind it and
// still carries the shelf.
module band_notch() {
    boxc(X_CAV - EPS, X_OUT + EPS, BAND_Y0, OUT_D + EPS, BAND_Z0, BAND_Z1);
    // Lead-in, so the band finds the slot instead of the wall end. Flared 1.5 mm
    // over a 2.5 mm run: shallower than 45 degrees in the build direction.
    hull() {
        boxc(X_CAV - EPS, X_OUT + EPS, OUT_D - CHAMFER, OUT_D - CHAMFER + EPS,
             BAND_Z0, BAND_Z1);
        boxc(X_CAV - EPS, X_OUT + EPS, OUT_D + 1 - EPS, OUT_D + 1,
             BAND_Z0 - CHAMFER, BAND_Z1 + CHAMFER);
    }
}

// --------------------------- the part --------------------------------------

module body() {
    // Top plate: the face that beds against the desk.
    boxc(-X_OUT, X_OUT, 0, OUT_D, Z_CAV_TOP, 0);
    // Rear wall: solid, it is the far end of the tray.
    boxc(-X_OUT, X_OUT, 0, BACK_T, Z_BOT, 0);

    for (m = [0, 1]) mirror([m, 0, 0]) {
        // Side wall, full height and full depth.
        boxc(X_CAV, X_OUT, 0, OUT_D, Z_BOT, 0);
        // Bottom shelf the PC rests on.
        boxc(X_SHELF, X_CAV, 0, OUT_D, Z_BOT, Z_FLOOR);
        // Mounting pads.
        for (cy = SCREW_YS) ear(cy);
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

    // Top-plate vents.
    translate([0, OUT_D / 2, Z_CAV_TOP - EPS])
        linear_extrude(height = TOP_T + 2 * EPS)
            vent_field(OUT_W - 2 * TOP_VENT_BORDER, OUT_D - 2 * TOP_VENT_BORDER,
                       VENT_W, VENT_LEN, VENT_ANGLE, VENT_RIB);

    // Side-wall vents, across the band of wall that faces the PC. The banded
    // wall's field stops one rib short of the slot; the other runs full length.
    mirror([BAND_SIDE > 0 ? 0 : 1, 0, 0]) side_vents(SIDE_VENT_Y0, BAND_VENT_Y1);
    mirror([BAND_SIDE > 0 ? 1 : 0, 0, 0]) side_vents(SIDE_VENT_Y0, PLAIN_VENT_Y1);

    // Slot for the band on the brick's side.
    mirror([BAND_SIDE > 0 ? 0 : 1, 0, 0]) band_notch();

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
    if (SHOW_BANK) {
        %translate([-BANK_W / 2, BACK_T, Z_FLOOR]) cube([BANK_W, BANK_D, BANK_H]);
        %mirror([BAND_SIDE > 0 ? 0 : 1, 0, 0])
            translate([BANK_W / 2, BANK_FRONT - BAND_DEPTH, BAND_Z - BAND_W / 2])
                cube([WALL + 2, BAND_DEPTH, BAND_W]);
    }
}
