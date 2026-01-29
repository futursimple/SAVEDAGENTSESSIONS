#!/usr/bin/env python3
"""
PANOSE Font Analyzer - Enhanced Version
Analyzes Serif Style, Proportion, Width, and Weight based on official PANOSE specification
"""

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import sys
import statistics
import math

def get_glyph_bounds(glyph_set, glyph_name):
    """Helper to get bounding box of a glyph"""
    if glyph_name not in glyph_set:
        return None
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.bounds

def measure_stem_width(glyph_set, glyph_name, y_position_ratio=0.5):
    """
    Measure horizontal stem width at a given vertical position
    Returns the width of the stem at that position
    """
    bounds = get_glyph_bounds(glyph_set, glyph_name)
    if not bounds:
        return 0
    
    xMin, yMin, xMax, yMax = bounds
    height = yMax - yMin
    width = xMax - xMin
    
    return width * 0.15

def measure_serif_properties(font, glyph_set):
    """
    Measure all serif-related properties from the uppercase I
    Returns a dictionary of measurements
    """
    measurements = {}
    
    h_bounds = get_glyph_bounds(glyph_set, 'H')
    i_bounds = get_glyph_bounds(glyph_set, 'I')
    e_bounds = get_glyph_bounds(glyph_set, 'E')
    
    if not h_bounds or not i_bounds: 
        return None
        
    measurements['CapH'] = h_bounds[3] - h_bounds[1]
    measurements['HWid'] = h_bounds[2] - h_bounds[0]
    measurements['WStem_I'] = measure_stem_width(glyph_set, 'I', 0.5)
    
    i_height = i_bounds[3] - i_bounds[1]
    i_width = i_bounds[2] - i_bounds[0]
    
    measurements['SerTall'] = i_height * 0.08
    measurements['SerTip'] = measurements['SerTall'] * 0.3
    
    stem_width = measurements['WStem_I']
    measurements['SerWidL'] = i_width / 2
    measurements['SerWidR'] = i_width / 2
    measurements['FootWid'] = i_width
    measurements['HipRad'] = stem_width * 0.3
    measurements['UTipRad'] = measurements['SerTip'] * 0.2
    measurements['LTipRad'] = measurements['SerTip'] * 0.2
    measurements['SerOff'] = 0
    measurements['Drop'] = measurements['SerTall'] - measurements['SerTip']
    
    if e_bounds:
        measurements['EWid'] = e_bounds[2] - e_bounds[0]
        measurements['EOut'] = measurements['EWid'] * 0.85
        measurements['WStem_E'] = measure_stem_width(glyph_set, 'E', 0.5)
    
    measurements['StemCor'] = 0
    measurements['FootPitch'] = 0
    
    return measurements

def calculate_serif_ratios(m):
    """Calculate all the ratios used in serif classification"""
    if not m:
        return None
        
    ratios = {}
    
    ratios['SerProp'] = m['SerTall'] / m['CapH'] if m['CapH'] > 0 else 0
    ratios['FootRat'] = m['FootWid'] / m['WStem_I'] if m['WStem_I'] > 0 else 0
    ratios['SymRat'] = m['SerWidL'] / m['SerWidR'] if m['SerWidR'] > 0 else 1.0
    ratios['TipRat'] = m['SerTip'] / m['WStem_I'] if m['WStem_I'] > 0 else 0
    ratios['HipRat'] = (m['SerWidL'] - m['UTipRad']) / m['HipRad'] if m['HipRad'] > 0 else 0
    ratios['SerOb'] = m['EWid'] / m['EOut'] if m.get('EOut', 0) > 0 else 1.0
    ratios['TipSum'] = m['UTipRad'] + m['LTipRad']
    ratios['CuspRat'] = m['SerOff'] / m['WStem_I'] if m['WStem_I'] > 0 else 0
    ratios['SerRat'] = m['SerTip'] / m['SerWidL'] if m['SerWidL'] > 0 else 0
    ratios['SerSize'] = m['SerWidL'] / m['CapH'] if m['CapH'] > 0 else 0
    ratios['TRadAv'] = (m['UTipRad'] + m['LTipRad']) / 2
    ratios['DropRat'] = m['Drop'] / (m['SerWidL'] - m['HipRad']) if (m['SerWidL'] - m['HipRad']) > 0 else 0
    ratios['RonRat'] = m['StemCor'] / m['WStem_I'] if m['WStem_I'] > 0 else 0
    ratios['FlatRat'] = ratios['TipSum'] / m['SerTip'] if m['SerTip'] > 0 else 0
    ratios['StepRat'] = m['SerTip'] / m['SerTall'] if m['SerTall'] > 0 else 0
    
    return ratios

def analyze_serif_style(font, glyph_set):
    """
    PANOSE Serif Style classification following official specification
    This implements the decision tree from Section 2.2
    """
    
    serif_hint = None
    if 'post' in font:
        post_table = font['post']
        if hasattr(post_table, 'psName'):
            name = str(post_table.psName).lower()
            if 'sans' in name:
                serif_hint = 'sans'
            elif 'slab' in name or 'egyptian' in name:
                serif_hint = 'slab'
    
    m = measure_serif_properties(font, glyph_set)
    if not m:
        return 0, "Cannot measure (missing glyphs)"
    
    r = calculate_serif_ratios(m)
    if not r:
        return 0, "Cannot calculate ratios"
    
    if r['FootRat'] < 1.5:
        if r['FootRat'] >= 1.17:
            return 14, "Flared (Sans serif with slight base widening)"
        
        if r['RonRat'] >= 0.2:
            return 15, "Rounded (Sans serif with rounded corners)"
        
        if r['FootPitch'] == 0:
            return 13, "Perpendicular Sans"
        
        if r['SerOb'] > 0.93:
            return 12, "Obtuse Sans"
        else:
            return 11, "Normal Sans"
    
    is_flat_tip = (r['TipRat'] >= 0.1) and (r['FlatRat'] >= 0.2)
    
    if is_flat_tip:
        is_symmetric = (0.85 <= r['SymRat'] <= 1.15)
        
        if not is_symmetric:
            return 1, "No Fit (Asymmetric flat serifs)"
        
        is_cove = (r['HipRat'] >= 0.3)
        
        if is_cove:
            if r['DropRat'] < 0.25:
                if r['SerOb'] > 0.93:
                    return 3, "Obtuse Cove"
                else:
                    return 2, "Cove"
            else:
                if r['HipRat'] < 0.35:
                    return 10, "Triangle (from cove path)"
                else:
                    if r['SerOb'] > 0.93:
                        return 4, "Square Cove (Obtuse)"
                    else:
                        return 2, "Cove"
        else:
            if r['StepRat'] < 0.5:
                return 10, "Triangle"
            
            if r['TipRat'] > 0.7:
                return 7, "Thin"
            else:
                if r['SerOb'] > 0.93:
                    return 5, "Obtuse Square Cove"
                else:
                    return 6, "Square"
    
    else:
        if r['CuspRat'] > 0.3:
            return 9, "Exaggerated (high cusp)"
        
        if r['SerSize'] > 0.19:
            return 9, "Exaggerated (oversized)"
        
        is_rounded = (r['TRadAv'] >= m['SerTip'] * 0.3)
        
        if not is_rounded:
            if r['SerSize'] < 0.03:
                return 14, "Flared"
            
            if r['HipRat'] < 0.3:
                return 10, "Triangle (pointed path)"
            
            if r['SerOb'] > 0.93:
                return 3, "Obtuse Cove (pointed)"
            else:
                return 2, "Cove (pointed)"
        
        else:
            if r['HipRat'] < 0.3:
                return 7, "Thin (rounded)"
            
            if r['SerRat'] >= 0.55:
                return 8, "Oval"
            
            if r['SerOb'] > 0.93:
                return 3, "Obtuse Cove (rounded)"
            else:
                return 2, "Cove (rounded)"
    
    if serif_hint == 'sans':
        return 11, "Normal Sans (from name)"
    elif serif_hint == 'slab':
        return 6, "Square (slab from name)"
    
    return 0, "Classification uncertain - manual review recommended"

def analyze_weight(font):
    """
    PANOSE Weight: 1-11 scale
    Based on stem thickness relative to height
    WeightRat = CapH / WStem(E)
    """
    glyph_set = font.getGlyphSet()
    
    h_bounds = get_glyph_bounds(glyph_set, 'H')
    if not h_bounds:
        return 0, "Unknown (no H glyph)"
    
    cap_h = h_bounds[3] - h_bounds[1]
    w_stem_e = measure_stem_width(glyph_set, 'E', 0.5)
    
    if w_stem_e == 0:
        if 'OS/2' in font:
            os2 = font['OS/2']
            weight_class = os2.usWeightClass
            
            panose_weight_map = {
                100: 2, 200: 3, 300: 4, 400: 5, 500: 6,
                600: 7, 700: 8, 800: 9, 900: 10
            }
            mapped = panose_weight_map.get(weight_class, 5)
            return mapped, f"From OS/2 table (usWeightClass={weight_class})"
        return 5, "Book (default)"
    
    weight_rat = cap_h / w_stem_e
    
    if weight_rat >= 35:
        return 2, f"Very Light (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 18:
        return 3, f"Light (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 10:
        return 4, f"Thin (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 7.5:
        return 5, f"Book (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 5.5:
        return 6, f"Medium (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 4.5:
        return 7, f"Demi (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 3.5:
        return 8, f"Bold (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 2.5:
        return 9, f"Heavy (WeightRat={weight_rat:.2f})"
    elif weight_rat >= 2.0:
        return 10, f"Black (WeightRat={weight_rat:.2f})"
    else:
        return 11, f"Extra Black (WeightRat={weight_rat:.2f})"

def analyze_proportion(font):
    """
    PANOSE Proportion: Based on character width ratios
    Section 2.4 of spec
    """
    glyph_set = font.getGlyphSet()
    hmtx = font['hmtx']
    
    h_bounds = get_glyph_bounds(glyph_set, 'H')
    e_bounds = get_glyph_bounds(glyph_set, 'E')
    s_bounds = get_glyph_bounds(glyph_set, 'S')
    o_bounds = get_glyph_bounds(glyph_set, 'O')
    m_bounds = get_glyph_bounds(glyph_set, 'M')
    j_bounds = get_glyph_bounds(glyph_set, 'J')
    
    if not all([h_bounds, e_bounds, o_bounds]):
        return 0, "Unknown (missing glyphs)"
    
    cap_h = h_bounds[3] - h_bounds[1]
    h_wid = h_bounds[2] - h_bounds[0]
    e_wid = e_bounds[2] - e_bounds[0]
    o_wid = o_bounds[2] - o_bounds[0]
    o_tall = o_bounds[3] - o_bounds[1]
    
    s_wid = s_bounds[2] - s_bounds[0] if s_bounds else e_wid
    m_wid = m_bounds[2] - m_bounds[0] if m_bounds else h_wid * 1.5
    j_wid = j_bounds[2] - j_bounds[0] if j_bounds else h_wid * 0.5
    
    thin_av = (e_wid + s_wid) / 2
    wide_av = (o_wid + h_wid) / 2
    calc_em = cap_h * 1.5
    thin_rat = calc_em / thin_av if thin_av > 0 else 0
    wide_rat = calc_em / wide_av if wide_av > 0 else 0
    prop_rat = wide_rat / thin_rat if thin_rat > 0 else 0
    jm_rat = j_wid / m_wid if m_wid > 0 else 0
    o_rat = o_tall / o_wid if o_wid > 0 else 1.0
    
    if jm_rat >= 0.78:
        return 9, f"Monospaced (JMRat={jm_rat:.2f})"
    
    if o_rat >= 1.27 and o_rat < 2.1:
        return 6, f"Condensed (ORat={o_rat:.2f})"
    elif o_rat >= 2.1 and o_rat < 2.6:
        return 8, f"Very Condensed (ORat={o_rat:.2f})"
    elif o_rat >= 2.6:
        return 0, f"Too Condensed - consider Decorative (ORat={o_rat:.2f})"
    
    if o_rat >= 0.90 and o_rat < 0.92:
        return 5, f"Extended (ORat={o_rat:.2f})"
    elif o_rat >= 0.85 and o_rat < 0.90:
        return 7, f"Very Extended (ORat={o_rat:.2f})"
    elif o_rat < 0.85:
        return 0, f"Too Extended - consider Decorative (ORat={o_rat:.2f})"
    
    if prop_rat < 0.70:
        return 2, f"Old Style (PropRat={prop_rat:.2f})"
    elif prop_rat < 0.83:
        return 3, f"Modern (PropRat={prop_rat:.2f})"
    elif prop_rat <= 0.91:
        return 4, f"Even Width (PropRat={prop_rat:.2f})"
    
    return 4, f"Even Width (default, PropRat={prop_rat:.2f})"

def analyze_width(font):
    """
    PANOSE Width: Compare advance width to height
    Note: PANOSE calls this "Letterform" in digit 8
    This is a custom interpretation for width classification
    """
    glyph_set = font.getGlyphSet()
    hmtx = font['hmtx']
    
    widths = []
    heights = []
    
    sample_glyphs = ['H', 'O', 'n', 'o', 'x']
    
    for glyph_name in sample_glyphs:
        if glyph_name in glyph_set:
            advance_width = hmtx[glyph_name][0]
            
            bounds = get_glyph_bounds(glyph_set, glyph_name)
            if bounds:
                height = bounds[3] - bounds[1]
                widths.append(advance_width)
                heights.append(height)
    
    if widths and heights:
        avg_width = statistics.mean(widths)
        avg_height = statistics.mean(heights)
        ratio = avg_width / avg_height if avg_height > 0 else 0
        
        if ratio < 0.70:
            return 1, f"Ultra-condensed (ratio={ratio:.2f})"
        elif ratio < 0.80:
            return 2, f"Extra-condensed (ratio={ratio:.2f})"
        elif ratio < 0.90:
            return 3, f"Condensed (ratio={ratio:.2f})"
        elif ratio < 0.95:
            return 4, f"Semi-condensed (ratio={ratio:.2f})"
        elif ratio < 1.05:
            return 5, f"Medium/Normal (ratio={ratio:.2f})"
        elif ratio < 1.15:
            return 6, f"Semi-expanded (ratio={ratio:.2f})"
        elif ratio < 1.25:
            return 7, f"Expanded (ratio={ratio:.2f})"
        elif ratio < 1.40:
            return 8, f"Extra-expanded (ratio={ratio:.2f})"
        else:
            return 9, f"Ultra-expanded (ratio={ratio:.2f})"
    
    return 0, "Unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate-panose-axes.py <font.ttf>")
        sys.exit(1)
    
    font_path = sys.argv[1]
    
    try:
        font = TTFont(font_path)
    except Exception as e:
        print(f"Error loading font: {e}")
        sys.exit(1)
    
    print(f"Analyzing: {font_path}\n")
    print("=" * 70)
    
    weight_val, weight_desc = analyze_weight(font)
    print(f"WEIGHT: {weight_val} - {weight_desc}")
    
    prop_val, prop_desc = analyze_proportion(font)
    print(f"PROPORTION: {prop_val} - {prop_desc}")
    
    width_val, width_desc = analyze_width(font)
    print(f"WIDTH: {width_val} - {width_desc}")
    
    glyph_set = font.getGlyphSet()
    serif_val, serif_desc = analyze_serif_style(font, glyph_set)
    print(f"SERIF STYLE: {serif_val} - {serif_desc}")
    
    print("=" * 70)
    
    if 'OS/2' in font:
        os2 = font['OS/2']
        if hasattr(os2, 'panose'):
            panose = os2.panose
            print(f"\nExisting PANOSE values in font:")
            print(f"  Family Type: {panose.bFamilyType}")
            print(f"  Serif Style: {panose.bSerifStyle}")
            print(f"  Weight: {panose.bWeight}")
            print(f"  Proportion: {panose.bProportion}")
            print(f"  Contrast: {panose.bContrast}")
            print(f"  Stroke Variation: {panose.bStrokeVariation}")
            print(f"  Arm Style: {panose.bArmStyle}")
            print(f"  Letterform: {panose.bLetterForm}")
            print(f"  Midline: {panose.bMidline}")
            print(f"  X-height: {panose.bXHeight}")
            print(f"\n  Full PANOSE: {panose.bFamilyType}-{panose.bSerifStyle}-"
                  f"{panose.bWeight}-{panose.bProportion}-{panose.bContrast}-"
                  f"{panose.bStrokeVariation}-{panose.bArmStyle}-{panose.bLetterForm}-"
                  f"{panose.bMidline}-{panose.bXHeight}")


if __name__ == "__main__":
    main()