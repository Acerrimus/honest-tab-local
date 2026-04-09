import {
  createGuestUserApi,
  createVolunteerUserApi,
  generateUsername,
} from "../../../steps/users";

describe("When the endpoint api/test/user is called", () => {
  it("should create a new user in the database", () => {
    createGuestUserApi(generateUsername()).then((response) => {
      expect(response.status).to.eq(201);
    });
  });

  it("should create a new volunteer in the database when a volunteer param is given", () => {
    createVolunteerUserApi(generateUsername()).then((response) => {
      expect(response.status).to.eq(201);
    });
  });
});
