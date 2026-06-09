from rag.rag_pipeline import RAGPipeline


def main():

    rag = RAGPipeline()

    print("Financial RAG Assistant")
    print("-----------------------")

    while True:

        query = input("\nAsk a question (or type exit): ")

        if query == "exit":
            break

        answer, contexts = rag.run(query)

        print("\nAnswer:\n")
        print(answer)

        print("\nSources:\n")
    
        for c in contexts:
            print(f"{c['source']} (page {c['page']})")


if __name__ == "__main__":
    main()