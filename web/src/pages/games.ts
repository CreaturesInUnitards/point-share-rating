import o from 'osyd'
import type { Children } from 'osyd'

import { Shell } from '../components/shell'
import type { PsrData, PsrGame } from '../state/psrState'
import type { OC } from '../types/appState'

type NameFn = (team: string) => string

export const teamNamer = (data: PsrData): NameFn => {
  const names: Record<string, string> = {}
  for (const t of data.teams) names[t.team] = t.name
  return team => names[team] ?? team
}

export const lineTxt = (g: PsrGame, p: number, nm: NameFn) =>
  Math.abs(p) < 0.05
    ? "pick 'em"
    : `${nm(p > 0 ? g.home : g.away)} by ${Math.abs(p).toFixed(1)}`

export const gradeResults = (results: PsrGame[]) => {
  let hits = 0
  const errs = results
    .map(g => {
      const actual = (g.hs ?? 0) - (g.as ?? 0)
      if ((g.pred > 0 && actual > 0) || (g.pred < 0 && actual < 0)) hits++
      return Math.abs(g.pred - actual)
    })
    .sort((a, b) => a - b)
  return { hits, median: errs[Math.floor(errs.length / 2)] ?? 0 }
}

const vfLineCell = (g: PsrGame, p: number, nm: NameFn) => [
  o('span.lg', lineTxt(g, p, nm)),
  o('span.sm',
    lineTxt(g, p, team => team),
  ),
]

const vfMatchup = (g: PsrGame, nm: NameFn, scored: boolean) => {
  const hWin = scored && (g.hs ?? 0) > (g.as ?? 0)
  const aWin = scored && (g.as ?? 0) > (g.hs ?? 0)
  const side = (team: string, label: string, won: boolean) => {
    const s = scored ? `${label} ${team === g.home ? g.hs : g.as}` : label
    return won ? o('b', s) : s
  }
  return [
    o('span.lg',
      side(g.away, nm(g.away), aWin),
      ' @ ',
      side(g.home, nm(g.home), hWin),
    ),
    o('span.sm', side(g.away, g.away, aWin), ' @ ', side(g.home, g.home, hWin)),
  ]
}

const vfSection = (title: string, legend: string, rows: Children) => [
  o('.sec', title),
  legend ? o('.legend', legend) : null,
  o('.tbl', rows),
]

const vfUpcoming = (data: PsrData, nm: NameFn) => {
  const games = data.games ?? {}
  const upcoming = games.upcoming ?? []
  if (!upcoming.length) return null
  const note =
    games.upSeason !== data.season
      ? 'preseason: every team starts at its reversion target'
      : 'psr line · market line for scale'
  return vfSection(
    `${games.upSeason} · week ${games.upWeek} · projected`,
    note,
    upcoming.map(g =>
      o('.grow',
        o('.mu', vfMatchup(g, nm, false)),
        o('.ln', vfLineCell(g, g.pred, nm)),
        o('.vg', g.vegas == null ? '' : `mkt: ${lineTxt(g, g.vegas, nm)}`),
      ),
    ),
  )
}

const vfResults = (data: PsrData, nm: NameFn) => {
  const games = data.games ?? {}
  const results = games.results ?? []
  if (!results.length) return null
  const { hits, median } = gradeResults(results)
  return vfSection(
    `${games.resSeason} · week ${games.resWeek} · results`,
    `called ${hits} of ${results.length} winners · median miss ${median.toFixed(1)} pts`,
    results.map(g => {
      const actual = (g.hs ?? 0) - (g.as ?? 0)
      const tie = actual === 0
      const hit = (g.pred > 0 && actual > 0) || (g.pred < 0 && actual < 0)
      const err = Math.abs(g.pred - actual)
      return o('.grow.res',
        o('.mu', vfMatchup(g, nm, true)),
        o('.ln', vfLineCell(g, g.pred, nm)),
        o('.er',
          { className: tie ? 'z' : hit ? 'u' : 'd' },
          `${tie ? '—' : hit ? '✓' : '✗'} ${err.toFixed(1)}`,
        ),
      )
    }),
  )
}

const vfFooter = (built: string): Children => [
  'Updated ',
  built,
  ' · projections come from the ',
  o(o.route.Link, { href: '/methods' }, 'documented model'),
  ': 1.71 points of margin per PSR, 1.70 for home field, minus the backup-QB penalty where it applies · data from ',
  o('a[href=https://github.com/nflverse]', 'nflverse'),
  '.',
]

export const GamesPage: OC = {
  view: ({ state: { $psr, $psrStatus } }) =>
    o(Shell,
      {
        page: 'games',
        wk: $psr ? `${$psr.season} season · games` : '',
        footer: vfFooter($psr?.built ?? ''),
      },
      o('p.sub',
        o('b', 'Every line here was produced before kickoff'),
        ', from ratings that use only earlier games — then graded in public, hits and misses alike. Lines are projected margins; the market’s line is shown for scale where one exists.',
      ),
      $psrStatus === 'error'
        ? o('p.sub', 'Games failed to load — refresh to try again.')
        : $psr
          ? [
              vfUpcoming($psr, teamNamer($psr)),
              vfResults($psr, teamNamer($psr)),
            ]
          : null,
    ),
}
