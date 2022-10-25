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