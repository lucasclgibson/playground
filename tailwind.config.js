const defaultTheme = require('tailwindcss/defaultTheme');

// tailwind.config.js
module.exports = {
  mode: 'jit',
  purge: ['./public/**/*.html', './src/**/*.{js,jsx,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['HK Grotesk', ...defaultTheme.fontFamily.sans]
      },
      colors: {
        'success': {
          DEFAULT: '#1BAC4C',
          '50': '#7FEBA4',
          '100': '#4EE481',
          '200': '#21D45E',
          '300': '#1FC758',
          '400': '#1DBA52',
          '500': '#1BAC4C',
          '600': '#168D3E',
          '700': '#116E31',
          '800': '#0C5023',
          '900': '#073115'
        },
        'danger': {
          DEFAULT: '#D74141',
          '50': '#F7D9D9',
          '100': '#F3C8C8',
          '200': '#ECA6A6',
          '300': '#E58484',
          '400': '#DE6363',
          '500': '#D74141',
          '600': '#B92727',
          '700': '#8B1D1D',
          '800': '#5C1313',
          '900': '#2E0A0A'
        },
        'peach': {
          DEFAULT: '#FC8459',
          '50': '#FED8CA',
          '100': '#FECFBE',
          '200': '#FEBDA5',
          '300': '#FDAA8B',
          '400': '#FD9772',
          '500': '#FC8459',
          '600': '#FC6E3B',
          '700': '#FC571D',
          '800': '#F64304',
          '900': '#D83A03'
        },
        'blue': {
          DEFAULT: '#2EA3FF',
          '50': '#E6F4FF',
          '100': '#D1EBFF',
          '200': '#A8D9FF',
          '300': '#80C7FF',
          '400': '#57B5FF',
          '500': '#2EA3FF',
          '600': '#0089F5',
          '700': '#006ABD',
          '800': '#004A85',
          '900': '#002B4D'
        },
        'ice': {
          DEFAULT: '#F5F7FA',
          '50': '#F5F7FA',
          '100': '#EEF2F7',
          '200': '#E1E7F0',
          '300': '#D3DCE9',
          '400': '#C5D1E2',
          '500': '#B8C6DB',
          '600': '#AABBD5',
          '700': '#9DB0CE',
          '800': '#8FA5C7',
          '900': '#819BC0'
        },
        'navy': {
          DEFAULT: '#373748',
          '50': '#82829E',
          '100': '#787897',
          '200': '#666685',
          '300': '#575770',
          '400': '#47475C',
          '500': '#373748',
          '600': '#333342',
          '700': '#2F2F3D',
          '800': '#2A2A37',
          '900': '#262631'
        },
        'blueberry': {
          DEFAULT: '#9156F0',
          '50': '#FFFFFF',
          '100': '#F3ECFD',
          '200': '#DBC7FA',
          '300': '#C3A1F7',
          '400': '#AA7CF4',
          '500': '#9156F0',
          '600': '#6F22EC',
          '700': '#5511C5',
          '800': '#3E0D91',
          '900': '#28085E'
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'fade-in': 'fadeIn .3s ease-in-out',
        'fade-in-up': 'fadeInUp .3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': {
            opacity: 0
          },
          '100%': {
            opacity: 100
          }
        },
        fadeInUp: {
          '0%': {
            opacity: 0,
            transform: 'translateY(15px)'
          },
          '100%': {
            opacity: 100,
            transform: 'translateY(0px)'
          }
        }
      }
    }
  }
  // specify other options here
};