import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: './src/api/swagger.yaml',
  output: {
    path: './src/api/client',
    format: 'prettier',
    lint: 'eslint',
  },
  plugins: [
    {
      name: '@hey-api/client-axios',
      runtimeConfigPath: '../customClient.ts',
    },
  ],
})
