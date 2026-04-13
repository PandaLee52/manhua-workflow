declare module 'mammoth' {
  interface ExtractRawTextResult {
    value: string
    messages: any[]
  }

  interface ExtractRawTextOptions {
    arrayBuffer?: ArrayBuffer
    path?: string
  }

  export function extractRawText(options: ExtractRawTextOptions): Promise<ExtractRawTextResult>
}

declare module 'pdfjs-dist' {
  export class GlobalWorkerOptions {
    static workerSrc: string
  }

  export interface PDFDocumentProxy {
    numPages: number
    getPage(pageNumber: number): Promise<PDFPageProxy>
  }

  export interface PDFPageProxy {
    getTextContent(): Promise<TextContent>
  }

  export interface TextContent {
    items: Array<{ str: string }>
  }

  export interface GetDocumentParams {
    data?: ArrayBuffer
    url?: string
  }

  export function getDocument(params: GetDocumentParams): { promise: Promise<PDFDocumentProxy> }

  export const version: string
}
