// frontend/src/api/index.js

const BASE_URL = 'http://127.0.0.1:5000/api'

async function request(path, params = {}) {
    const url = new URL(BASE_URL + path)

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            url.searchParams.set(key, value)
        }
    })

    const resp = await fetch(url.toString())
    if (!resp.ok) {
        throw new Error(`HTTP error ${resp.status}`)
    }
    return resp.json()
}

export function fetchCities(region) {
    return request('/cities', region ? { region } : {})
}

export function fetchHouses(params) {
    return request('/houses', params)
}

export function fetchPriceTrend(cityId) {
    return request('/price_trend', { city_id: cityId })
}
