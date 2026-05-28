# **Programmatic Integration of the Meta Threads API: Comprehensive Architecture for Webhook-Driven Publishing and Live Post Engagement**

## **Instagram-to-Threads Identity Linking and OAuth 2.0 Authorization Lifecycle**

The technical foundation of Meta's Threads API relies on its direct integration with the existing Instagram infrastructure.1 Programmatic interactions on Threads are executed by leveraging a user’s Instagram account identity, meaning that a developer cannot create a standalone Threads-only API endpoint.2 Instead, the Threads profile handles and content permissions are structurally mapped to the corresponding Instagram user ID, requiring a linked profile setup during initial onboarding.2  
To establish this programmatic link, the application must orchestrate an OAuth 2.0 authorization code flow, utilizing Instagram's secure authorization servers to grant access.1 This flow begins when the user is redirected to the Instagram authorization endpoint to approve the requested permission scopes.1 The request structure must explicitly define the Client ID, a registered Redirect URI (pointing to the host server), the response type, and the target scopes 4:  
![][image1]

| Authorization Parameter | Architectural Role and Constraints |
| :---- | :---- |
| client\_id | The public application identifier generated within the Meta Developer Portal.5 |
| redirect\_uri | The verified callback endpoint on the Railway instance designed to catch authorization codes.4 |
| scope | A comma-delimited array of requested access permissions.4 |
| response\_type | Must be set to code to request an authorization code.4 |

The specific capabilities granted to the access token are defined by granular permission scopes.1 To build a platform that publishes content, tracks interactions, and manages live conversations, the application must request a specific matrix of permissions.7 Developers must request only the minimum required scopes to improve the chances of passing Meta’s App Review, which is required before the application can move from development to production mode.1

| Permission Scope | Functional Capabilities and Applications |
| :---- | :---- |
| threads\_basic | Grants read access to user profile metadata, published media IDs, and supports token refresh requests.1 |
| threads\_content\_publish | Allows the application to prepare draft containers and publish text, images, and video posts.1 |
| threads\_read\_replies | Enables the webhook and UI to retrieve replies, comments, and conversation structures.7 |
| threads\_manage\_replies | Permits programmatic reply posting, reply hiding/showing, and reply control settings.7 |
| threads\_manage\_insights | Accesses analytics metrics, including view counts, likes, reposts, and shares.7 |
| threads\_share\_to\_instagram | Authorizes the application to cross-share published Threads posts to a linked Instagram account.6 |

Once the user approves these permissions, Meta's authorization server redirects the client to the application's Redirect URI, appending a temporary authorization code as a query parameter.5 The backend server must immediately capture this code and perform a token exchange sequence to transition from short-lived authorization to long-term access 5:

1. **Short-Lived Access Token Swap**: The server executes an HTTP POST request to https://graph.threads.net/oauth/access\_token, passing the Client ID, Client Secret, the redirect URI, and the authorization code.4 This returns a short-lived user access token, which is valid for approximately one hour.6  
2. **Long-Lived Access Token Exchange**: To prevent requiring frequent user logins, the backend must immediately trade this one-hour token for a long-lived user access token.6 This exchange is performed by sending a GET request to the token exchange endpoint with the client secret and the short-lived token, yielding a token valid for 60 days.6  
3. **Automated Token Refresh Pipeline**: Long-lived tokens can be programmatically refreshed before they expire.6 A refresh call is permitted only after the active long-lived token is at least 24 hours old.6 Successful execution extends the token's validity for another 60 days.6 This cycle can be automated using a recurring background task.6

If a private user profile connects to the application, its permissions are subject to a strict 90-day expiration limit, requiring a complete re-authorization flow once the window closes.6

## **The Two-Step Asynchronous Publishing Pipeline and Media Constraints**

The Threads API does not support direct multipart media uploads via HTTP POST requests.6 Instead, it uses a two-step, asynchronous, container-based publishing pipeline similar to Instagram's Reels publishing flow.3 This design ensures that media rendering and optimization are handled asynchronously by Meta's infrastructure.6  
The standard media publishing flow is executed as follows:

1. **Media Hosting**: The application hosts the target image file on a publicly accessible web server, Amazon S3 bucket, or CDN.6 Meta's backend servers must be able to reach this URL over the public internet to download the file.2  
2. **Draft Container Creation**: The application sends a POST request to the POST /{user\_id}/threads endpoint.5 The JSON payload must specify the media\_type as IMAGE, provide the public image\_url, and include the caption text.1 Upon receiving the request, Meta's servers validate the payload and return a unique draft media container ID.1  
3. **Asynchronous Polling and Processing**: After issuing the container ID, Meta's servers download and optimize the image file in the background.6 If the download fails (for example, due to a private URL or firewalled CDN), the container status is set to FAILED\_DOWNLOADING\_VIDEO.6 Because the API does not send a webhook event when media processing finishes, the application must poll the container status endpoint once per minute for up to 5 minutes before attempting to publish.3  
4. **Broadcast Publishing**: Once the status endpoint confirms the container is ready, the application sends a POST request to POST /{user\_id}/threads\_publish, passing the container ID as the creation\_id parameter.2 This final step publishes the post to the user's live profile.1

For text-only posts, the API provides a streamlined shortcut.6 By including the parameter auto\_publish\_text in the container creation request, developers can publish text content in a single step, bypassing the standard two-step container flow.6  
All media assets and text payloads sent through this pipeline must adhere to strict platform specifications to prevent API errors 2:

| Content Dimension | Platform Specification / Limit | Architectural Rationale |
| :---- | :---- | :---- |
| **Text Length** | Maximum of 500 characters.2 | Maintains the platform's short-form, text-focused format.2 |
| **Link Attachments** | Maximum of 5 URLs (inline links \+ link attachments).6 | Exceeding this limit triggers a THREADS\_API\_\_LINK\_LIMIT\_EXCEEDED error.6 |
| **Hashtags** | Maximum of 1 hashtag per post.2 | Designed to prevent tag spam and keep feeds readable.2 |
| **Image File Size** | Maximum of 8 MB.2 | Keeps network transfers efficient and limits processing overhead.2 |
| **Image Formats** | JPEG, PNG, GIF, and WEBP.2 | Restricting formats ensures consistent cross-platform rendering.2 |
| **Image Dimensions** | Width: 320 px to 1440 px.6 | Keeps media dimensions aligned with mobile app viewports.6 |
| **Image Aspect Ratio** | Between 4:5 and 1.91:1.2 | Ensures images display cleanly without unwanted cropping.2 |
| **Video File Size** | Maximum of 1 GB.3 | Prevents processing delays on large uploads.10 |
| **Video Duration** | 3 seconds to 300 seconds (5 minutes).2 | Balances short-form video engagement with network performance.2 |
| **Carousel Items** | 2 to 20 media items.6 | Carousels count as a single post toward daily limits.6 |

Overall API usage is managed using a rolling, impression-based call rate limit calculated per user-app pair over a 24-hour window.6 This calculation uses a multiplier formula that scales based on the user's content reach 6:  
![][image2]  
Meta enforces a minimum safety floor of 10 impressions for this formula, ensuring that even newly registered profiles with zero reach have a minimum allocation of 48,000 API calls per day.6 The platform also monitors and limits server processing time 6:  
![][image3]  
![][image4]  
Beyond these structural API call limits, Meta restricts publishing actions per profile within a rolling 24-hour window.6 These action limits are outlined in the table below:

| Programmatic Action | 24-Hour Cap | Operational Monitoring Endpoint |
| :---- | :---- | :---- |
| **Published Posts** | 250 posts (carousels count as one).6 | Query quota\_usage via /threads\_publishing\_limit.6 |
| **Conversation Replies** | 1,000 replies.6 | Query reply\_quota\_usage via /threads\_publishing\_limit.6 |
| **Profile Deletions** | 100 deletions.6 | Query delete\_quota\_usage via /threads\_publishing\_limit.6 |
| **Location Searches** | 500 searches.6 | Query location\_search\_quota\_usage via /threads\_publishing\_limit.6 |

Rather than hardcoding these boundaries, the application should dynamically query the active user limits by sending a GET request to /v1.0/{threads-user-id}/threads\_publishing\_limit.6

## **Webhook Architecture, Real-Time Ingestion, and Webhook-Filtering Strategies**

Programmatically tracking comment feeds and managing live user interactions requires a webhook architecture registered within the Meta Developer Dashboard.11

### **Webhook Verification Handshake**

When registering or updating a webhook URL in the developer portal, Meta's servers verify ownership of the endpoint by executing an HTTP GET request to the target URI.12 This request includes three query parameters 12:

* hub.mode: Set to the literal string subscribe.14  
* hub.verify\_token: A secret, user-defined verification token configured in both the developer portal and the local application environment.12  
* hub.challenge: A random cryptographic string generated by Meta.12

The receiver must validate that the incoming hub.verify\_token matches the configured secret.12 If it matches, the endpoint must return the exact hub.challenge string in the response body.13 To protect against Cross-Site Scripting (XSS) vulnerabilities, the HTTP response headers of the handshake must be structured as follows 13:

HTTP  
HTTP/1.1 200 OK  
Content-Type: text/plain; charset=utf-8  
X-Content-Type-Options: nosniff

### **Event Notification Payloads**

Once verified, Meta pushes real-time events to the endpoint using HTTP POST requests.12 Meta batches events to reduce server-to-server overhead, structuring the payload under nested arrays: body.entry and entry.changes.12

JSON  
{  
  "object": "threads",  
  "entry":  
    }  
  \]  
}

The server-side router must parse this JSON payload, looping through the entries and changes to extract the media\_id (representing the comment or reply ID) and the parent\_id (representing the post being replied to).12 To prevent retry loops, the webhook router must handle its processing asynchronously, returning an HTTP 200 OK response within 3 seconds.12

### **Webhook Noise Mitigation**

A common challenge when integrating Meta APIs is handling high-volume status webhooks.15 When subscribing to the replies or mentions field, Meta sends notifications for real incoming messages as well as status updates (such as sent, delivered, or read receipts).15 These status updates can be up to 5 times more frequent than actual user interactions.15

                     (GET/POST Request)  
Meta Server \-----------------------------------\>  
                                                          |  
                                           (Is Status Notification?)  
                                           /                       \\  
                                                             \[No\]  
                                         /                           \\  
                           (Respond 200 OK & Discard)     (Forward to Railway App Queue)  
                                                                       |  
                                                                       v  
                                                              

To prevent processing redundant status updates, developers should implement a pre-filtering layer.15 This can be built using an edge handler (such as a Cloudflare Worker) or custom server-side middleware to intercept Meta payloads, forward only real user messages or replies to the Railway Hono queue, and immediately drop redundant status entries with a 200 OK.15 This approach ensures the backend queue only processes valid user interactions, saving compute resources.15

## **Live Post Engagement and Content Moderation Endpoints**

Interacting with live content requires utilizing a broader set of endpoints beyond basic publishing.8 The Threads API supports a complete loop of engagement actions—including replying, liking, reposting, quoting, and comment moderation 8:

* **Replying to Posts**: To reply to an existing post, create a media container with the reply\_to\_id parameter set to the target post's ID.8 This structures the new post as a nested response within the thread.8  
* **Controlling Replies**: When creating a container, developers can restrict who is allowed to reply by setting the reply\_control parameter.3 This parameter supports three options: everyone, accounts\_you\_follow, or mentioned\_only.3  
* **Liking and Unliking**: To like or unlike a post, send a POST request to /{post\_id}/likes or its inverse endpoint.8  
* **Reposting and Sharing**: Content can be programmatically reshared to a user's timeline by sending a POST request to the repost endpoint.8  
* **Quoting Content**: To quote a post, create a media container containing the target post's ID and the commentary text.8  
* **Moderation and Hiding**: Developers can hide or show replies programmatically using the manage\_reply interface, passing the target reply ID and a boolean hide parameter.8 This capability is useful for building automated moderation tools or customer support filters.8

| Engagement Action | HTTP Method & Target API Endpoint | Required & Optional Payload Parameters |
| :---- | :---- | :---- |
| **Create Reply** | POST /v1.0/{user\_id}/threads.5 | media\_type: "TEXT", text, reply\_to\_id (Required).8 reply\_control (Optional).3 |
| **Manage Reply (Hide/Show)** | POST /v1.0/{reply\_id}/manage\_reply.8 | hide: true (to hide comment) | hide: false (to unhide comment).8 |
| **Like Post** | POST /v1.0/{post\_id}/likes.8 | No additional payload parameters required.8 |
| **Unlike Post** | DELETE /v1.0/{post\_id}/likes.8 | No additional payload parameters required.8 |
| **Repost Thread** | POST /v1.0/{post\_id}/repost.8 | No additional payload parameters required.8 |
| **Retrieve Mentions** | GET /v1.0/{user\_id}/mentions.8 | fields (Optional array of fields to retrieve), limit (Optional pagination limit).8 |

## **Full-Stack Integration Architecture on Railway**

To support programmatic publishing and live interactions, the deployment architecture is split into a Hono-powered Node.js/TypeScript server and an in-memory Redis database.17  
The Hono web framework handles HTTP requests, serves the frontend dashboard, and receives webhook notifications.17 Incoming webhook events are offloaded to BullMQ, a Redis-backed queue system that manages background jobs.17 This design ensures the webhook endpoint can acknowledge Meta's payload within the required 3-second window, leaving the actual API execution to background workers.12

TypeScript  
// server.ts  
import { Hono } from 'hono';  
import { Queue, Worker } from 'bullmq';  
import IORedis from 'ioredis';

const app \= new Hono();

// Connect to the managed Railway Redis instance  
const redisConnection \= new IORedis(process.env.REDIS\_URL || 'redis://127.0.0.1:6379');  
const taskQueue \= new Queue('ThreadsTaskQueue', { connection: redisConnection });

/\*\*  
 \* Webhook Verification Handler (GET)  
 \* Responds to Meta's security challenge and returns the hub.challenge in plain text.  
 \*/  
app.get('/webhook', async (c) \=\> {  
  const query \= c.req.query();  
  const mode \= query\['hub.mode'\];  
  const token \= query\['hub.verify\_token'\];  
  const challenge \= query\['hub.challenge'\];

  if (mode \=== 'subscribe' && token \=== process.env.WEBHOOK\_VERIFY\_TOKEN) {  
    c.status(200);  
    c.header('Content-Type', 'text/plain');  
    c.header('X-Content-Type-Options', 'nosniff');  
    return c.text(challenge);  
  }  
    
  return c.text('Forbidden', 403);  
});

/\*\*  
 \* Webhook Event Notification Endpoint (POST)  
 \* Accepts incoming events, filters out noise, and queues valid responses.  
 \*/  
app.post('/webhook', async (c) \=\> {  
  try {  
    const payload \= await c.req.json();  
    const entries \= payload?.entry ||;

    for (const entry of entries) {  
      const changes \= entry?.changes ||;  
      for (const change of changes) {  
        // Filter out status updates and ensure we only process real incoming replies  
        if (change.field \=== 'replies' && change.value?.text) {  
          await taskQueue.add('ProcessIncomingReply', {  
            replyId: change.value.media\_id,  
            parentId: change.value.parent\_id,  
            text: change.value.text,  
            username: change.value.username  
          });  
        }  
      }  
    }  
      
    // Acknowledge receipt within the 3-second limit to prevent retry storms  
    return c.text('EVENT\_RECEIVED', 200);  
  } catch (error) {  
    return c.text('PROCESSING\_FAILED\_BUT\_ACKNOWLEDGED', 200);  
  }  
});

/\*\*  
 \* Dashboard API Route (POST)  
 \* Receives publishing requests from the custom UI.  
 \*/  
app.post('/api/publish', async (c) \=\> {  
  const body \= await c.req.json();  
  const { imageUrl, caption } \= body;

  if (\!imageUrl ||\!caption) {  
    return c.json({ error: 'Image URL and Caption are required' }, 400);  
  }

  const job \= await taskQueue.add('PublishImageThread', {  
    imageUrl,  
    caption,  
    userId: process.env.THREADS\_USER\_ID,  
    token: process.env.LONG\_LIVED\_ACCESS\_TOKEN  
  });

  return c.json({ success: true, jobId: job.id });  
});

/\*\*  
 \* Dashboard UI Endpoint (GET)  
 \* Serves a simple, reactive HTML panel to trigger posts and monitor interactions.  
 \*/  
app.get('/', (c) \=\> {  
  return c.html(\`  
    \<\!DOCTYPE html\>  
    \<html lang="en"\>  
    \<head\>  
      \<meta charset="UTF-8"\>  
      \<meta name="viewport" content="width=device-width, initial-scale=1.0"\>  
      \<title\>Threads API Management Dashboard\</title\>  
      \<script src="https://cdn.tailwindcss.com"\>\</script\>  
    \</head\>  
    \<body class="bg-slate-900 text-slate-100 min-h-screen font-sans flex flex-col items-center py-10"\>  
      \<main class="w-full max-w-2xl px-4"\>  
        \<header class="mb-8 text-center"\>  
          \<h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600"\>Threads API Control Center\</h1\>  
          \<p class="text-slate-400 mt-2"\>Programmatic Publishing and Live Conversation Monitor\</p\>  
        \</header\>  
          
        \<section class="bg-slate-800 rounded-lg p-6 shadow-xl border border-slate-700 mb-6"\>  
          \<h2 class="text-xl font-bold mb-4 text-purple-300"\>Publish Image Thread\</h2\>  
          \<div class="space-y-4"\>  
            \<div\>  
              \<label class="block text-sm font-semibold mb-1"\>Public Image URL\</label\>  
              \<input type="url" id="imgUrl" placeholder="https://yourcdn.com/image.png" class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-pink-500"\>  
            \</div\>  
            \<div\>  
              \<label class="block text-sm font-semibold mb-1"\>Caption / Text (Max 500 Chars)\</label\>  
              \<textarea id="caption" rows="3" placeholder="Write your post content..." class="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-pink-500"\>\</textarea\>  
            \</div\>  
            \<button onclick="submitPost()" class="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-2 px-4 rounded transition duration-200"\>Broadcast to Threads\</button\>  
          \</div\>  
        \</section\>

        \<section class="bg-slate-800 rounded-lg p-6 shadow-xl border border-slate-700"\>  
          \<h2 class="text-xl font-bold mb-4 text-pink-300"\>Live Post Interactions Feed\</h2\>  
          \<div id="interactionFeed" class="space-y-3 max-h-60 overflow-y-auto pr-2"\>  
            \<p class="text-slate-500 text-sm text-center py-4"\>Waiting for incoming comment webhooks...\</p\>  
          \</div\>  
        \</section\>  
      \</main\>

      \<script\>  
        async function submitPost() {  
          const imageUrl \= document.getElementById('imgUrl').value;  
          const caption \= document.getElementById('caption').value;  
          if (\!imageUrl ||\!caption) return alert('Fill in all fields');  
            
          const res \= await fetch('/api/publish', {  
            method: 'POST',  
            headers: { 'Content-Type': 'application/json' },  
            body: JSON.stringify({ imageUrl, caption })  
          });  
          const data \= await res.json();  
          if (data.success) {  
            alert('Job successfully added to backend queue\!');  
            document.getElementById('imgUrl').value \= '';  
            document.getElementById('caption').value \= '';  
          } else {  
            alert('Failed to schedule job');  
          }  
        }  
      \</script\>  
    \</body\>  
    \</html\>  
  \`);  
});

/\*\*  
 \* Background Worker Processing Pipeline  
 \* Handles container creation, status polling, and publishing.  
 \*/  
const taskWorker \= new Worker('ThreadsTaskQueue', async (job) \=\> {  
  if (job.name \=== 'PublishImageThread') {  
    const { imageUrl, caption, userId, token } \= job.data;

    // 1\. Create Draft Container  
    const containerRes \= await fetch(\`https://graph.threads.net/v1.0/${userId}/threads\`, {  
      method: 'POST',  
      headers: { 'Content-Type': 'application/json' },  
      body: JSON.stringify({  
        media\_type: 'IMAGE',  
        image\_url: imageUrl,  
        text: caption,  
        access\_token: token  
      })  
    });

    const containerData \= await containerRes.json();  
    if (\!containerData.id) {  
      throw new Error(\`Failed to create draft container: ${JSON.stringify(containerData)}\`);  
    }

    const containerId \= containerData.id;

    // 2\. Poll Status until state is 'FINISHED'  
    let isProcessed \= false;  
    let attempts \= 0;  
    const maxAttempts \= 5;

    while (\!isProcessed && attempts \< maxAttempts) {  
      await new Promise((resolve) \=\> setTimeout(resolve, 60000)); // Wait 60 seconds  
      attempts++;

      const statusRes \= await fetch(\`https://graph.threads.net/v1.0/${containerId}?fields=status,error\_message\&access\_token=${token}\`);  
      const statusData \= await statusRes.json();

      if (statusData.status \=== 'FINISHED') {  
        isProcessed \= true;  
      } else if (statusData.status \=== 'ERROR' || statusData.error\_message) {  
        throw new Error(\`Asynchronous media processing failed: ${statusData.error\_message}\`);  
      }  
    }

    if (\!isProcessed) {  
      throw new Error('Media processing timeout. Meta servers failed to fetch media in time.');  
    }

    // 3\. Publish Container  
    const publishRes \= await fetch(\`https://graph.threads.net/v1.0/${userId}/threads\_publish\`, {  
      method: 'POST',  
      headers: { 'Content-Type': 'application/json' },  
      body: JSON.stringify({  
        creation\_id: containerId,  
        access\_token: token  
      })  
    });

    const publishData \= await publishRes.json();  
    return { livePostId: publishData.id };  
  }  
    
  if (job.name \=== 'ProcessIncomingReply') {  
    const { replyId, parentId, text, username } \= job.data;  
    // Implement custom moderation or auto-response logic here  
    console.log(\`Processing incoming reply from @${username}: "${text}" on parent ${parentId}\`);  
  }  
}, { connection: redisConnection });

export default app;

## **Conclusions and Systems Deployment Guidelines**

Deploying a custom Threads API integration on Railway requires careful planning to handle rate limits, background processing, and token lifecycles.5 When deploying this architecture, engineers should follow these core production guidelines:

### **Automate Token Refreshes to Prevent Outages**

Because long-lived tokens expire after 60 days, configure a scheduled background task to refresh active tokens every 30 days.6 The backend should automatically listen for HTTP 401 errors and Graph API Error Code 190\.5 If a token is invalidated, the system should pause outgoing API calls and alert administrators via email or Discord, avoiding unnecessary API rejections.5

### **Use Exponential Backoff for Robust Retry Logic**

If the application hits rate limits (HTTP 429\) or server errors (HTTP 500), configure the background worker to use an exponential backoff strategy.5 Scaling the delay between retries prevents spamming Meta's endpoints and protects your API quota 5:  
![][image5]

### **Protect Webhooks with Signal Filtering**

Meta bundles real user comments and automatic status updates (sent, delivered, read) into the same webhook subscriptions.15 To avoid hitting database write limits or exhausting your background worker queue, implement an edge-level filter or fast-path middleware.15 This filter should inspect incoming payloads, discard status updates, and forward only valid user actions to the main database.15

### **Respect Daily Action and Publishing Caps**

Keep the application aligned with Threads' daily limits, which restrict accounts to 250 posts and 1,000 replies per 24 hours.6 Implement local counters in Redis to track daily usage, and use the dynamic publishing limit endpoint to verify remaining quotas before executing new jobs 6:  
GET /v1.0/{threads-user-id}/threads\_publishing\_limit

#### **Works cited**

1. Threads API Documentation 2026: Complete Developer Guide \- Zernio, accessed May 27, 2026, [https://zernio.com/blog/threads-api](https://zernio.com/blog/threads-api)  
2. Threads API Integration: Authorization, Posting, & Analytics with Ayrshare, accessed May 27, 2026, [https://www.ayrshare.com/blog/threads-api-integration-authorization-posting-analytics-with-ayrshare/](https://www.ayrshare.com/blog/threads-api-integration-authorization-posting-analytics-with-ayrshare/)  
3. Post to Threads via API — Threads Integration \- Postproxy, accessed May 27, 2026, [https://postproxy.dev/platforms/threads/](https://postproxy.dev/platforms/threads/)  
4. threads-api | Skills Marketplace \- LobeHub, accessed May 27, 2026, [https://lobehub.com/zh/skills/rawveg-skillsforge-marketplace-threads-api](https://lobehub.com/zh/skills/rawveg-skillsforge-marketplace-threads-api)  
5. Threads Posting API: OAuth Setup & Code Examples \[2026\] \- Zernio, accessed May 27, 2026, [https://zernio.com/blog/threads-posting-api](https://zernio.com/blog/threads-posting-api)  
6. Threads API Pricing 2026: Free, but Rate-Limited \- Blotato, accessed May 27, 2026, [https://www.blotato.com/blog/threads-api-pricing](https://www.blotato.com/blog/threads-api-pricing)  
7. Threads API | Documentation | Postman API Network, accessed May 27, 2026, [https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)  
8. baguskto/threads-mcp · GitHub \- GitHub, accessed May 27, 2026, [https://github.com/baguskto/threads-mcp](https://github.com/baguskto/threads-mcp)  
9. README.md \- artisbautra/threads-api-ai · GitHub, accessed May 27, 2026, [https://github.com/artisbautra/threads-api-ai/blob/main/README.md](https://github.com/artisbautra/threads-api-ai/blob/main/README.md)  
10. How to Post to Threads via API \- Postproxy, accessed May 27, 2026, [https://postproxy.dev/how-to/post-to-threads-api/](https://postproxy.dev/how-to/post-to-threads-api/)  
11. Facebook Messenger API: Build Conversational Experiences \- Zernio, accessed May 27, 2026, [https://zernio.com/blog/facebook-messenger-api](https://zernio.com/blog/facebook-messenger-api)  
12. Building a Real-Time Facebook Page Comment Listener Using Webhooks (Node.js \+ Graph API) | by Hasiniwij | Emojot Engineering | Medium, accessed May 27, 2026, [https://medium.com/emojot-engineering/building-a-real-time-facebook-page-comment-listener-using-webhooks-node-js-graph-api-17dad90e992e](https://medium.com/emojot-engineering/building-a-real-time-facebook-page-comment-listener-using-webhooks-node-js-graph-api-17dad90e992e)  
13. Webhooks \- Developers \- Dropbox.com, accessed May 27, 2026, [https://www.dropbox.com/developers/reference/webhooks](https://www.dropbox.com/developers/reference/webhooks)  
14. Ingesting Facebook webhooks (challenge & verification) | WebhookRelay, accessed May 27, 2026, [https://webhookrelay.com/blog/ingesting-facebook-webhooks/](https://webhookrelay.com/blog/ingesting-facebook-webhooks/)  
15. How to stop WhatsApp Cloud API status webhooks from eating your n8n executions — using a Cloudflare Worker (for generic Webhook node users) \- Tips & Tricks, accessed May 27, 2026, [https://community.n8n.io/t/how-to-stop-whatsapp-cloud-api-status-webhooks-from-eating-your-n8n-executions-using-a-cloudflare-worker-for-generic-webhook-node-users/294956](https://community.n8n.io/t/how-to-stop-whatsapp-cloud-api-status-webhooks-from-eating-your-n8n-executions-using-a-cloudflare-worker-for-generic-webhook-node-users/294956)  
16. Threads Api | APIs.io Providers, accessed May 27, 2026, [https://providers.apis.io/providers/threads-api/](https://providers.apis.io/providers/threads-api/)  
17. Application Webhook Template \- TypeScript app deployed on Railway \- Front Community, accessed May 27, 2026, [https://community.front.com/developer-discussion-39/application-webhook-template-typescript-app-deployed-on-railway-2056](https://community.front.com/developer-discussion-39/application-webhook-template-typescript-app-deployed-on-railway-2056)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,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>

[image5]: <data:image/png;base64,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>