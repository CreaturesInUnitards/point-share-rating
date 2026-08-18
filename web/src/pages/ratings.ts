import o from 'osyd'
import type { Children, ClosureComponent } from 'osyd'

import { Shell } from '../components/shell'
import type { PsrTeam } from '../state/psrState'
import type { Actions, AppState, OC } from '../types/appState'

const SPAN = 8 // bar half-range in rating points
const REPO_URL = 'https://github.com/CreaturesInUnitards/point-share-rating'

export const vfSpark = (traj: number[]) => {
  const w = 72
  const h = 18
  const min = Math.min(...traj)
  const rng = Math.max(Math.max(...traj) - min, 1.5)
  const pts = traj
    .map(
      (v, i) =>
        `${((i / Math.max(traj.length - 1, 1)) * w).toFixed(1)},${(h - 2 - ((v - min) / rng) * (h - 4)).toFixed(1)}`,
    )
    .join(' ')
  const mid = h - 2 - ((50 - min) / rng) * (h - 4)
  return o('svg.spark[aria-hidden=true]',
    { width: w, height: h },
    mid > 0 && mid < h
      ? o('line', {
          x1: 0,
          y1: mid.toFixed(1),
          x2: w,
          y2: mid.toFixed(1),
          stroke: '#D8DAD4',
          'stroke-dasharray': '2,3',
        })
      : null,
    o('polyline', {
      points: pts,
      fill: 'none',
      stroke: '#10151C',
      'stroke-width': 1.4,
    }),
  )
}

const vfPart = (
  k: string,
  v: number,
  n: string,
  opts?: { signed?: boolean; sum?: boolean },
) => {
  const s = opts?.signed && v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)
  const vc = opts?.signed ? (v > 0.05 ? 'u' : v < -0.05 ? 'd' : '') : ''
  return o('.part',
    { className: opts?.sum ? 'sum' : undefined },
    o('.k', k),
    o('.v', { className: vc || undefined }, s),
    o('.n', n),
  )
}

const vfDetail = (t: PsrTeam) => {
  const vsAvg = t.rating - 50
  return o('.detail',
    o('.eq',
      vfPart('Point share', t.raw, `${t.games} games`),
      o('.op', '+'),
      vfPart('Schedule', t.schedule, t.scheduleNote, { signed: true }),
      o('.op', '+'),
      vfPart('Recency', t.recency, t.recencyNote, { signed: true }),
      o('.op', '+'),
      vfPart('Reversion', t.prior, t.priorNote, { signed: true }),
      o('.op', '='),
      vfPart(
        'Rating',
        t.rating,
        `${vsAvg > 0 ? '+' : ''}${vsAvg.toFixed(1)} PSR vs avg`,
        { sum: true },
      ),
    ),
    o('.sent',
      'Worth about ',
      o('b', `${Math.abs(vsAvg * 1.7).toFixed(1)} points of margin`),
      ` ${vsAvg >= 0 ? 'above' : 'below'} an average team on a neutral field. `,
      Math.abs(t.qbPts) >= 1.5
        ? [
            'Current starter is worth ',
            o('b',
              `${t.qbPts > 0 ? '+' : ''}${t.qbPts.toFixed(1)} points of margin per game`,
            ),
            ' vs an average QB. ',
          ]
        : null,
      'Season path:',
      vfSpark(t.traj),
    ),
  )
}

const TeamRow: ClosureComponent<
  { t: PsrTeam; rank: number },
  AppState,
  Actions
> = () => {
  const gsOpen = o.getSet(false)
  const toggle = () => gsOpen(!gsOpen())
  return {
    view: ({ props: { t, rank } }) => {
      const dev = t.rating - 50
      const w = Math.min(Math.abs(dev) / SPAN, 1) * 50
      const left = dev >= 0 ? 50 : 50 - w
      const open = gsOpen()
      const dcls = t.delta > 0.05 ? 'u' : t.delta < -0.05 ? 'd' : 'z'
      const dtxt =
        t.delta > 0.05
          ? `▲ ${t.delta.toFixed(1)}`
          : t.delta < -0.05
            ? `▼ ${Math.abs(t.delta).toFixed(1)}`
            : '—'
      return [
        o('.row[tabindex=0][role=listitem]',
          {
            className: open ? 'open' : undefined,
            'aria-expanded': String(open),
            onclick: toggle,
            onkeydown: (e: KeyboardEvent) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                toggle()
              }
            },
          },
          o('.rk', rank),
          o('.tm',
            t.name,
            o('small', t.qbPts <= -2 ? 'backup range QB' : `QB: ${t.qb}`),
          ),
          o('.bar',
            o('.axis'),
            o('.dev', {
              style: {
                left: `${left}%`,
                width: `${w}%`,
                background: dev >= 0 ? 'var(--up)' : 'var(--down)',
              },
            }),
          ),
          o('.rt', t.rating.toFixed(1)),
          o('.dl', { className: dcls }, dtxt),
          o('.chev', '›'),
        ),
        open ? vfDetail(t) : null,
      ]
    },
  }
}

const vfFooter = (built: string): Children => [
  'Updated ',
  built,
  ' · data from ',
  o('a[href=https://github.com/nflverse]', 'nflverse'),
  ' · every number on this page is reproducible from the ',
  o(`a[href=${REPO_URL}]`, 'open pipeline'),
  '. Validated out-of-sample over 22 seasons; the receipts — including what didn’t work — are on the ',
  o(o.route.Link, { href: '/methods' }, 'methods page'),
  '.',
]

export const RatingsPage: OC = {
  view: ({ state: { $psr, $psrStatus } }) =>
    o(Shell,
      {
        page: 'ratings',
        wk: $psr ? `${$psr.season} season · through week ${$psr.week}` : '',
        footer: vfFooter($psr?.built ?? ''),
      },
      o('p.sub',
        o('b', 'Point Share Rating'),
        ' — a team’s share of the scoring, adjusted for schedule, recency, and quarterback. ',
        o('b', '50 is league average.'),
        ' Each PSR above 50 is worth about 1.7 points of scoreboard margin on a neutral field. Tap any team to see how its number is built.',
      ),
      o('.legend',
        o('span', 'below average'),
        o('span', '50'),
        o('span', 'above average'),
      ),
      $psrStatus === 'error'
        ? o('p.sub', 'Ratings failed to load — refresh to try again.')
        : o('.tbl[role=list]',
            ($psr?.teams ?? []).map((t, i) =>
              o(TeamRow, { key: t.team, t, rank: i + 1 }),
            ),
          ),
    ),
}
