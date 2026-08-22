import { chinaModule } from './china'
import { usaModule } from './usa'
import { singaporeModule } from './singapore'
import { taiwanModule } from './taiwan'
import { japanModule } from './japan'
import type { CountryModule } from './types'

export * from './types'
export { chinaModule, getChinaDetailAnalysis } from './china'

export const COUNTRY_MODULES: Record<string, CountryModule> = {
  CN: chinaModule,
  US: usaModule,
  SG: singaporeModule,
  TW: taiwanModule,
  JP: japanModule,
}

export const COUNTRY_ORDER = ['CN', 'US', 'SG', 'TW', 'JP']
