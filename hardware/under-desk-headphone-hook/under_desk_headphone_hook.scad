// ---------------------------------------------------------------------------
// Under-desk headphone hook
//
// A J that screws to the underside of a desk and hangs headphones off it. One
// screw, through a pad that sits flat against the desk.
//
// The whole thing is a profile swept across its width, so it prints lying on
// its side: nothing overhangs, and the layers run along the arm rather than
// across it, which is the direction the load pulls.
//
//   x = width,  y = out from the back of the pad,  z = height, 0 = desk
//
// Render:  openscad -o hook.stl under_desk_headphone_hook.scad
// ---------------------------------------------------------------------------

/* [Hook] */
WIDTH  = 30.0;           // across; wide enough not to crease a headband
BAR    = 7.0;            // bar thickness
DROP   = 40.0;           // straight arm below the desk before the cradle
THROAT = 38.0;           // centreline gap. What matters is what is left after
                         // the bar: THROAT - BAR has to swallow a padded band
TIP    = 18.0;           // how far the far side rises to stop it slipping off
ARM_Y  = 26.0;           // how far forward the arm hangs, from the pad's back

/* [Pad] */
PAD_D = 34.0;            // front to back
PAD_T = 6.0;             // thick enough to countersink into
PAD_R = 2.0;             // edge rounding in section; must clear PAD_T/2

/* [Fastener] One #8 or M4 flat-head wood screw */
SCREW_D    = 5.0;
HEAD_D     = 9.5;
CSK_ANGLE  = 90.0;
SCREW_Y    = 15.0;       // from the back of the pad; set so a driver clears the arm
DRIVER_CLR = 1.5;

/* [Output] */
PRINT_ORIENTATION = true;    // on its side, which is how it prints
$fn = 64;

// --------------------------- derived --------------------------------------

R = THROAT / 2;                  // cradle radius, centreline
CSK_DEPTH = (HEAD_D - SCREW_D) / 2 / tan(CSK_ANGLE / 2);
BOT = -DROP - R;                 // lowest point of the centreline
EPS = 0.01;

assert(PAD_T > CSK_DEPTH + 1.5, "too little pad left under the countersink");
assert(PAD_R < PAD_T / 2 && PAD_R < PAD_D / 2,
       "PAD_R is larger than the pad it rounds - the pad would come out empty");
assert(ARM_Y + BAR / 2 <= PAD_D, "the arm hangs off the front of the pad");
assert(HEAD_D + 4 < PAD_D, "no room for a screw head on the pad");
assert(SCREW_Y + HEAD_D / 2 + DRIVER_CLR <= ARM_Y - BAR / 2,
       "the arm crowds the screw head; move the screw back or the arm forward");
assert(SCREW_Y - HEAD_D / 2 > 1, "the screw head runs off the back of the pad");
assert(TIP < DROP, "the tip rises past the desk");
assert(THROAT - BAR >= 30, "the throat will not swallow a padded headband");

// --------------------------- helpers --------------------------------------

// A rounded bar swept along a centreline: hull each pair of points with a
// circle of the bar's thickness. Keeps every corner radiused, which is what
// you want against a headband.
module bar(pts) {
    for (i = [0 : len(pts) - 2])
        hull() {
            translate(pts[i]) circle(d = BAR);
            translate(pts[i + 1]) circle(d = BAR);
        }
}

// --------------------------- the part --------------------------------------

// Centreline: down the arm, round the cradle, back up to the tip.
ARC = [for (a = [0 : 10 : 180]) [ARM_Y + R - R * cos(a), -DROP - R * sin(a)]];

module profile() {
    // Mounting pad.
    translate([PAD_R, -PAD_T + PAD_R])
        offset(r = PAD_R) square([PAD_D - 2 * PAD_R, PAD_T - 2 * PAD_R]);
    // Arm, cradle, tip.
    bar(concat([[ARM_Y, -PAD_T / 2]], ARC,
               [[ARM_Y + 2 * R, -DROP + TIP]]));
}

module hook() {
    difference() {
        // profile is drawn in (y, z); sweep it across the width
        translate([-WIDTH / 2, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 90])
            linear_extrude(height = WIDTH) profile();
        // Screw, countersunk from below.
        translate([0, SCREW_Y, -PAD_T - EPS]) {
            cylinder(h = PAD_T + 2 * EPS, d = SCREW_D);
            cylinder(h = CSK_DEPTH + EPS, d1 = HEAD_D + 2 * EPS, d2 = SCREW_D);
        }
    }
}

if (PRINT_ORIENTATION) translate([0, 0, WIDTH / 2]) rotate([0, 90, 0]) hook();
else hook();
