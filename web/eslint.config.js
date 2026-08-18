import eslint from '@eslint/js'
import osydPlugin from 'eslint-plugin-osyd'
import tseslint from 'typescript-eslint'

export default [
  // Base JS recommendations
  eslint.configs.recommended,

  // TypeScript recommendations (parser + plugin via typescript-eslint)
  ...tseslint.configs.recommended,

  {
    plugins: { osyd: osydPlugin },
    rules: {
      'arrow-body-style': ['error', 'as-needed'],
      'osyd/closure-prop-alias-init-prefix': 'error',
      'osyd/no-invalid-component-props': 'error',
      'osyd/prettier': [
        'error',
        {
          prettierOptions: {
            arrowParens: 'avoid',
            printWidth: 80,
            tabWidth: 2,
            useTabs: false,
            semi: false,
            singleQuote: true,
            bracketSpacing: true,
            bracketSameLine: false,
            trailingComma: 'all',
          },
        },
      ],
    },
  },

  // Ignore common generated directories
  {
    ignores: ['dist', 'coverage', 'node_modules'],
  },
]
