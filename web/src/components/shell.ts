import o from 'osyd'
import type { Children } from 'osyd'

import type { OC } from '../types/appState'

export type PageId = 'ratings' | 'games' | 'methods'

const NAV: Array<{ id: PageId; href: string; label: string }> = [
  { id: 'ratings', href: '/', label: 'Ratings' },
  { id: 'games', href: '/games', label: 'Games' },
  { id: 'methods', href: '/methods', label: 'Methods & receipts' },
]

export const Shell: OC<{ page: PageId; wk: Children; footer: Children }> = {
  view: ({ props: { page, wk, footer }, children }) =>
    o(`.wrap.pg-${page}`,
      o('header', o('.mark', 'PSR', o('span', '.')), o('.wk', wk)),
      o('nav',
        NAV.map(({ id, href, label }) =>
          o(o.route.Link,
            { key: id, href, className: id === page ? 'on' : undefined },
            label,
          ),
        ),
      ),
      children,
      o('footer', footer),
    ),
}
