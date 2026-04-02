import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../../steps/orders";
import { generateUsername } from "../../../steps/users";

describe("When the endpoint api/test/orders is called", () => {
  it("should return the orders for the specified user", () => {
    const username = generateUsername();
    const orderDetails = generateOrderDetails(username);
    createUserOrderAPI(orderDetails);
    getUserOrdersAPI(username).then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body.orders).to.have.lengthOf(1);
      expect(response.body.orders[0].order_id).to.eq(orderDetails.order_id);
    });
  });
});
