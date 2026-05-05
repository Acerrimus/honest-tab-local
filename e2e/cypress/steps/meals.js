export function getTotalServedInt(text) {
  return parseInt(text.split(" ").at(-1));
}

export function createGuestDinnerMealForTodayApi(username, receiver) {
  return cy.request({
    method: "POST",
    url: "http://app:8000/api/test/meals/dinner/today",
    qs: { username, receiver },
  });
}

export function getTodaysDinnerMealsApi() {
  return cy.request({
    url: "http://app:8000/api/test/meals/dinner/today",
  });
}
