import type { PsrGame } from '../state/psrState'
import { gradeResults, lineTxt } from './games'

const nm = (t: string) => ({ BUF: 'Bills', NYJ: 'Jets' })[t] ?? t

const game = (over: Partial<PsrGame>): PsrGame => ({
  away: 'NYJ',
  home: 'BUF',
  pred: 3.5,
  ...over,
})

test('lineTxt names the favored side with the margin', () => {
  expect(lineTxt(game({}), 3.5, nm)).toBe('Bills by 3.5')
  expect(lineTxt(game({}), -2.1, nm)).toBe('Jets by 2.1')
  expect(lineTxt(game({}), 0.0, nm)).toBe("pick 'em")
})

test('gradeResults counts winner calls and median miss', () => {
  const results = [
    game({ pred: 3.5, hs: 24, as: 17 }), // hit, err 3.5
    game({ pred: -4.0, hs: 30, as: 20 }), // miss, err 14
    game({ pred: 7.0, hs: 21, as: 14 }), // hit, err 0
  ]
  const { hits, median } = gradeResults(results)
  expect(hits).toBe(2)
  expect(median).toBe(3.5)
})

test('gradeResults handles an empty slate', () => {
  expect(gradeResults([])).toEqual({ hits: 0, median: 0 })
})
