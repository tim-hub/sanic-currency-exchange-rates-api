import http from 'k6/http'

import { check, sleep } from 'k6'

export const options = {
  stages: [
    { duration: '1s', target: 20 },
    { duration: '3s', target: 10 },
  ],
}

export default function () {

  const res = http.get('http://127.0.0.1:8000/api/latest')

  check(res, { 'status was 200': (r) => r.status === 200 })

  sleep(0.1)

}
