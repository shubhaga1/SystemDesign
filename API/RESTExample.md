The following are the available API endpoints and their functionalities:

1. **Authentication (auth):**
- **POST /auth/login:** This endpoint allows users to log in and obtain an authentication token. [[1](https://example.com/auth/login)]

2. **Users:**
- **GET /users/@{username}:** Retrieve details of a user based on their username. [[2](https://example.com/users/@{username})]
- **GET /users/{userid}:** Retrieve details of a user based on their user ID. [[3](https://example.com/users/{userid})]
- **POST /users:** Create a new user. [[4](https://example.com/users)]
- **PATCH /users/{userid} (Requires authentication):** Update user details such as bio, name, image, etc. [[5](https://example.com/users/{userid})]
- **PUT /users/{userid}/follow (Requires authentication):** Follow a specific user. (No specific reference found)
- **DELETE /users/{userid}/follow (Requires authentication):** Unfollow a specific user. (No specific reference found)
- **GET /users/{userid}/followers:** Retrieve a list of all followers of a user. [[6](https://example.com/users/{userid}/followers)]
- **GET /users/{userid}/followees:** Retrieve a list of all users followed by a specific user. [[7](https://example.com/users/{userid}/followees)]

3. **Posts:**
- **GET /posts:** Retrieve a list of posts. It may include query parameters for filtering results. [[8](https://example.com/posts)]
- **GET /posts/{postid}:** Retrieve details of a specific post using its ID. [[9](https://example.com/posts/{postid})]
- **POST /posts (Requires authentication):** Create a new post. [[10](https://example.com/posts)]
- **DELETE /posts/{postid} (Requires authentication):** Delete a specific post. [[11](https://example.com/posts/{postid})]
- **PUT /posts/{postid}/like (Requires authentication):** Like a specific post. [[12](https://example.com/posts/{postid}/like)]
- **DELETE /posts/{postid}/like (Requires authentication):** Remove a like from a specific post. [[13](https://example.com/posts/{postid}/like)]

4. **Hashtags:**
- **GET /hashtags:** Retrieve a list of top hashtags (default top 10). [[14](https://example.com/hashtags)]
- **GET /hashtags/{tag}/posts:** Retrieve all posts associated with a specific hashtag. [[15](https://example.com/hashtags/{tag}/posts)]
