//! SIMD-friendly complex linear algebra for fixed 4×4 Hermitian × ℂ⁴.
//! Uses `wide::f32x4` for portable SIMD on stable Rust (PRD: SIMD-accelerated RK4).

use num_complex::Complex32;
use wide::f32x4;

#[inline]
fn cadd(a: Complex32, b: Complex32) -> Complex32 {
    Complex32::new(a.re + b.re, a.im + b.im)
}

#[inline]
fn cmul(a: Complex32, b: Complex32) -> Complex32 {
    Complex32::new(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re)
}

/// Hermitian 4×4 (row-major `h[row][col]`) times `psi` → `out`.
#[inline]
pub fn hermitian_matvec4(h: &[[Complex32; 4]; 4], psi: &[Complex32; 4], out: &mut [Complex32; 4]) {
    for row in 0..4 {
        let mut sum = Complex32::new(0.0, 0.0);
        for (col, pc) in psi.iter().enumerate() {
            sum = cadd(sum, cmul(h[row][col], *pc));
        }
        out[row] = sum;
    }
}

/// Same as [`hermitian_matvec4`] with SIMD-accumulated partial products per row.
#[inline]
pub fn hermitian_matvec4_simd(
    h: &[[Complex32; 4]; 4],
    psi: &[Complex32; 4],
    out: &mut [Complex32; 4],
) {
    for row in 0..4 {
        let h = &h[row];
        let p = psi;

        let r01 = f32x4::new([
            h[0].re * p[0].re - h[0].im * p[0].im,
            h[0].re * p[0].im + h[0].im * p[0].re,
            h[1].re * p[1].re - h[1].im * p[1].im,
            h[1].re * p[1].im + h[1].im * p[1].re,
        ]);
        let r23 = f32x4::new([
            h[2].re * p[2].re - h[2].im * p[2].im,
            h[2].re * p[2].im + h[2].im * p[2].re,
            h[3].re * p[3].re - h[3].im * p[3].im,
            h[3].re * p[3].im + h[3].im * p[3].re,
        ]);
        let s01 = r01.as_array_ref()[0] + r01.as_array_ref()[2];
        let s0i = r01.as_array_ref()[1] + r01.as_array_ref()[3];
        let s23 = r23.as_array_ref()[0] + r23.as_array_ref()[2];
        let s2i = r23.as_array_ref()[1] + r23.as_array_ref()[3];
        out[row] = Complex32::new(s01 + s23, s0i + s2i);
    }
}

/// `y += a * x` for four complex components.
#[inline]
pub fn simd_axpy_c4(a: f32, x: &[Complex32; 4], y: &mut [Complex32; 4]) {
    let xr = f32x4::new([x[0].re, x[1].re, x[2].re, x[3].re]);
    let xi = f32x4::new([x[0].im, x[1].im, x[2].im, x[3].im]);
    let yr = f32x4::new([y[0].re, y[1].re, y[2].re, y[3].re]);
    let yi = f32x4::new([y[0].im, y[1].im, y[2].im, y[3].im]);
    let nr = yr + xr * f32x4::splat(a);
    let ni = yi + xi * f32x4::splat(a);
    let nr = nr.as_array_ref();
    let ni = ni.as_array_ref();
    for i in 0..4 {
        y[i] = Complex32::new(nr[i], ni[i]);
    }
}

/// `dst = src` (SIMD copy).
#[inline]
pub fn simd_copy_c4(src: &[Complex32; 4], dst: &mut [Complex32; 4]) {
    let sr = f32x4::new([src[0].re, src[1].re, src[2].re, src[3].re]);
    let si = f32x4::new([src[0].im, src[1].im, src[2].im, src[3].im]);
    let r = sr.as_array_ref();
    let i = si.as_array_ref();
    for j in 0..4 {
        dst[j] = Complex32::new(r[j], i[j]);
    }
}

/// Schrödinger rhs: `dψ/dt = -i H ψ` (ℏ = 1).
#[inline]
pub fn schrodinger_rhs_from_hpsi(h_psi: &[Complex32; 4], out: &mut [Complex32; 4]) {
    let re = f32x4::new([h_psi[0].re, h_psi[1].re, h_psi[2].re, h_psi[3].re]);
    let im = f32x4::new([h_psi[0].im, h_psi[1].im, h_psi[2].im, h_psi[3].im]);
    let out_re = im;
    let out_im = -re;
    let or = out_re.as_array_ref();
    let oi = out_im.as_array_ref();
    for j in 0..4 {
        out[j] = Complex32::new(or[j], oi[j]);
    }
}

/// `work = H * psi`, then `out = -i * work`.
#[inline]
pub fn apply_tdse_rhs(
    h: &[[Complex32; 4]; 4],
    psi: &[Complex32; 4],
    work: &mut [Complex32; 4],
    out: &mut [Complex32; 4],
) {
    hermitian_matvec4_simd(h, psi, work);
    schrodinger_rhs_from_hpsi(work, out);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_matvec() {
        let id = [
            [
                Complex32::new(1.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
            ],
            [
                Complex32::new(0.0, 0.0),
                Complex32::new(1.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
            ],
            [
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(1.0, 0.0),
                Complex32::new(0.0, 0.0),
            ],
            [
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(0.0, 0.0),
                Complex32::new(1.0, 0.0),
            ],
        ];
        let psi = [
            Complex32::new(1.0, 0.0),
            Complex32::new(0.0, 0.0),
            Complex32::new(0.0, 0.0),
            Complex32::new(0.0, 0.0),
        ];
        let mut out = [Complex32::new(0.0, 0.0); 4];
        hermitian_matvec4_simd(&id, &psi, &mut out);
        assert_eq!(out, psi);
    }
}
