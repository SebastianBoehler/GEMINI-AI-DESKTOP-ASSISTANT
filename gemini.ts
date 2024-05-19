import {
  VertexAI,
  HarmCategory,
  HarmBlockThreshold,
  GenerateContentRequest,
  FunctionDeclaration,
  FunctionDeclarationSchemaType,
  RetrievalTool,
  Tool,
  Content,
} from "@google-cloud/vertexai";
import fs from "fs";
import dotenv from "dotenv";
dotenv.config();

// Initialize Vertex with your Cloud project and location
const vertex_ai = new VertexAI({
  project: process.env.GOOGLE_PROJECT_ID || "",
  location: "us-central1",
});

const model = "gemini-1.5-pro-preview-0514";

const generativeModel = vertex_ai.getGenerativeModel({
  model: model,
  generationConfig: {
    maxOutputTokens: 8192,
    temperature: 1,
    topP: 0.95,
  },
  safetySettings: [
    {
      category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
      threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
      category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
      threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
      category: HarmCategory.HARM_CATEGORY_HARASSMENT,
      threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
      category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
      threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
  ],
});

const getWeather: FunctionDeclaration = {
  name: "getWeather",
  description: "Get the weather in a specific location",
  parameters: {
    type: FunctionDeclarationSchemaType.OBJECT,
    properties: {
      location: {
        type: FunctionDeclarationSchemaType.STRING,
        description: "The location to get the weather for",
        nullable: false,
      },
    },
    required: ["location"],
  },
};

const fetchTool: FunctionDeclaration = {
  name: "fetch",
  description: `
    Fetch data from a given URL. To load any website, use this tool. please load direct files like *.html. load from public sites. only in a row. Returns the fetched website as text.
    Needs the url as full string with protocol and params like https://www.google.com/search?q=hello
    `,
  parameters: {
    type: FunctionDeclarationSchemaType.OBJECT,
    properties: {
      url: {
        type: FunctionDeclarationSchemaType.STRING,
        description: "The URL to fetch data from",
        nullable: false,
      },
    },
    required: ["url"],
  },
};

const googleRetrival: RetrievalTool = {
  retrieval: {
    vertexAiSearch: {
      datastore: "",
    },
  },
};

const input: string =
  "load the site hb-capital.app for em and tell me what the company does";

const imageData = fs.readFileSync("image.jpg", "base64");

const contents: Content[] = [
  {
    role: "user",
    parts: [
      // {
      //   inlineData: {
      //     mimeType: "image/jpeg",
      //     data: imageData,
      //   },
      // },
      {
        text: input,
      },
    ],
  },
];

async function generateContent(tools: Tool[], contents: Content[]) {
  const req: GenerateContentRequest = {
    contents,
    tools,
  };

  const streamingResp = await generativeModel.generateContentStream(req);

  for await (const item of streamingResp.stream) {
    // console.log(
    //   "stream chunk: " + JSON.stringify(item.candidates?.[0].content) + "\n"
    // );
  }

  const aggregatedResponse = await streamingResp.response;
  const functionCalls = aggregatedResponse.candidates?.[0].content.parts.filter(
    (parts) => parts.functionCall
  );
  console.log(JSON.stringify(aggregatedResponse.candidates?.[0].content.parts));
  console.log(aggregatedResponse.candidates?.[0].content.parts.length);

  if (functionCalls) {
    for (const call of functionCalls) {
      if (call.functionCall?.name === "fetch") {
        // @ts-ignore
        const url = call.functionCall.args.url;
        const response = await fetch(url);
        const text = await response.text();
        contents.push({
          role: "function",
          parts: [
            {
              functionCall: {
                name: "fetch",
                args: {
                  url: url,
                },
              },
            },
          ],
        });
        contents.push({
          role: "function",
          parts: [
            {
              functionResponse: {
                name: "fetch",
                response: {
                  text: text,
                },
              },
            },
          ],
        });
        generateContent([], contents);
      }
      if (call.functionCall?.name === "getWeather") {
        // @ts-ignore
        const location = call.functionCall.args.location;
        console.log(location);
        generateContent([], contents);
      }
    }
  }
}

generateContent(
  [
    {
      functionDeclarations: [
        // getWeather,
        fetchTool,
      ],
    },
  ],
  contents
);
