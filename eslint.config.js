const neostandard = require('neostandard')
const eslintPluginPrettierRecommended = require('eslint-plugin-prettier/recommended')

module.exports = [
  ...neostandard({
    env: ['browser', 'jquery'],
    globals: {
      getCookie: 'readonly'
    }
  }),
  eslintPluginPrettierRecommended
]
