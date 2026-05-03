import { generateOrderDetails } from "../../../steps/orders";
import { generateUsername } from "../../../steps/users";

describe("When POST /api/test/orders is called with valid details", () => {
  it("should create a test order in the database", () => {
    const orderDetails = generateOrderDetails(generateUsername());
    cy.request({
      method: "POST",
      url: "http://localhost:8000/api/test/orders",
      qs: orderDetails,
    }).then((response) => {
      expect(response.status).to.eq(201);
      expect(response.body.message).to.eq("Test order created successfully");
      expect(response.body.order_id).to.eq(orderDetails.order_id);
    });
  });
});
