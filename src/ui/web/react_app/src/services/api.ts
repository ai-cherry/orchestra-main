import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v2',
    prepareHeaders: (headers) => {
      // Add any default headers here
      headers.set('Content-Type', 'application/json');
      return headers;
    },
  }),
  tagTypes: ['Search', 'File', 'Multimedia', 'Operator'],
  endpoints: (builder) => ({
    // Search endpoints
    search: builder.query({
      query: ({ mode, query, limit = 20 }) => ({
        url: '/search',
        params: { mode, q: query, limit },
      }),
      providesTags: ['Search'],
    }),
    
    // File ingestion endpoints
    uploadFile: builder.mutation({
      query: (formData) => ({
        url: '/ingest-file',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['File'],
    }),
    
    // Multimedia endpoints
    generateImage: builder.mutation({
      query: (data) => ({
        url: '/multimedia/generate-image',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Multimedia'],
    }),
    
    // Operator mode endpoints
    createOperatorTask: builder.mutation({
      query: (task) => ({
        url: '/operator/tasks',
        method: 'POST',
        body: task,
      }),
      invalidatesTags: ['Operator'],
    }),
  }),
});

export const {
  useSearchQuery,
  useUploadFileMutation,
  useGenerateImageMutation,
  useCreateOperatorTaskMutation,
} = api;
