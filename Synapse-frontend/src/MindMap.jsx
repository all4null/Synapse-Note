import React, { useRef, useEffect } from 'react';
import { Transformer } from 'markmap-lib';
import { Markmap } from 'markmap-view';
import { Toolbar } from 'markmap-toolbar';
import 'markmap-toolbar/dist/style.css';

const transformer = new Transformer();

export default function MindMap({ markdown }) {
    const svgRef = useRef(null);
    const mmRef = useRef(null);
    const wrapperRef = useRef(null);

    useEffect(() => {
        if (svgRef.current && markdown) {
            // 1. Transform Markdown -> Mindmap Data
            const { root } = transformer.transform(markdown);

            // 2. Render or Update Markmap
            if (mmRef.current) {
                mmRef.current.setData(root);
                mmRef.current.fit();
            } else {
                mmRef.current = Markmap.create(svgRef.current, {
                    autoFit: true,
                    // zoom: true, 
                    // pan: true
                }, root);

                // Add Toolbar
                if (wrapperRef.current) {
                    const toolbar = new Toolbar();
                    toolbar.attach(mmRef.current);
                    toolbar.setBrand(false); // Hide brand
                    wrapperRef.current.append(toolbar.render());
                }
            }
        }
    }, [markdown]);

    return (
        <div ref={wrapperRef} style={{ width: '100%', height: '500px', position: 'relative', border: '1px solid #eee', borderRadius: '8px', overflow: 'hidden' }}>
            <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
        </div>
    );
}
