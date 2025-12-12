// frontend/src/api/index.js

const BASE_URL = 'http://127.0.0.1:8000/api/v1'

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

export function fetchHouses(params) {
    return request('/houses', params)
}

export function fetchHouseDetail(houseId) {
    return request(`/houses/${houseId}`)
}

export function fetchCityStatistics() {
    return request('/statistics/cities')
}

export function fetchPriceTrend(city, months = 3) {
    return request('/statistics/price-trend', { city, months })
}

export function fetchDistrictStatistics(city) {
    return request('/statistics/districts', { city })
}
