import {
  createGuestDinnerMealForTodayApi,
  getTodaysDinnerMealsApi,
} from "../../../steps/meals";
import { generateReceiver } from "../../../steps/orders";
import { generateUsername } from "../../../steps/users";
describe("When POST /api/meals/dinner/today is called with valid details", () => {
  it("that meal will be created and returned in the response from GET /api/meals/dinner/today", () => {
    const username = generateUsername();
    const receiver = generateReceiver(username);
    createGuestDinnerMealForTodayApi(username, receiver).then(
      (createGuestDinnerMealForTodayResponse) => {
        getTodaysDinnerMealsApi().then((todaysDinnerMealsResponse) => {
          expect(
            todaysDinnerMealsResponse.body.meals.filter(
              (meal) =>
                meal.meal_id ===
                createGuestDinnerMealForTodayResponse.body.meal_id,
            ),
          ).to.be.lengthOf(1);
        });
      },
    );
  });
});
