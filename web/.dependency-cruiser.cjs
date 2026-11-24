/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      from: {},
      to: { circular: true },
    },
    {
      name: 'feature-isolation',
      comment:
        'A feature is reached through its public index.ts, never by reaching into its files.',
      severity: 'error',
      from: { path: '^src/features/([^/]+)/' },
      to: { path: '^src/features/(?!$1)[^/]+/(?!index\\.ts$).+' },
    },
    {
      name: 'only-data-imports-supabase',
      comment: 'The Supabase client lives behind src/data, so the rest of the web never sees it.',
      severity: 'error',
      from: { pathNot: '^src/data/' },
      to: { path: 'node_modules/@supabase/supabase-js' },
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: 'tsconfig.json' },
    exclude: { path: '\\.test\\.tsx?$' },
  },
}
