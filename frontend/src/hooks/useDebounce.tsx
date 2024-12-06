import { useState, useEffect } from "react";

function useSearchDebounce(query: string, delay: number): string {
    const [debouncedQuery, setDebouncedQuery] = useState(query);

    useEffect(() => {
        // Set up a debounce timer
        const timer = setTimeout(() => {
            setDebouncedQuery(query);
        }, delay);

        // Clean up the timer on component unmount or when `query` or `delay` changes
        return () => clearTimeout(timer);
    }, [query, delay]);

    return debouncedQuery;
}

export default useSearchDebounce;
