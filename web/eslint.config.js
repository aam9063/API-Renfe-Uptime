import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'

const USEEFFECT_MESSAGE =
  'Data access goes through TanStack Query hooks in src/data, never through an effect.'
const SUPABASE_MESSAGE = 'Only src/data may import the Supabase client.'

export default tseslint.config(
  { ignores: ['dist/', 'node_modules/', 'playwright-report/', 'test-results/', '.evidence/'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2023,
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            { name: 'react', importNames: ['useEffect'], message: USEEFFECT_MESSAGE },
            { name: '@supabase/supabase-js', message: SUPABASE_MESSAGE },
          ],
        },
      ],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  {
    files: ['**/*.cjs'],
    languageOptions: { sourceType: 'commonjs', globals: { ...globals.node } },
  },
  {
    files: ['src/data/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        { paths: [{ name: 'react', importNames: ['useEffect'], message: USEEFFECT_MESSAGE }] },
      ],
    },
  },
  {
    files: ['src/features/**/*.{ts,tsx}'],
    rules: {
      'no-magic-numbers': [
        'error',
        { ignore: [0, 1], ignoreArrayIndexes: true, ignoreDefaultValues: true },
      ],
    },
  },
  {
    files: ['**/*.test.{ts,tsx}'],
    rules: {
      'no-magic-numbers': 'off',
    },
  },
)
