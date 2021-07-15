# nio: [Ni]ck's [O]NNX Accelerator

An example accelerator to demonstrate the usage and flexibility of NNFlex.


# Design

This accelerator uses:
* 1 external memory (one-read and one-write at a time, pipelined, `nio_mem_piped.py`)
* An MxN grid of Tiles (a tile takes it's logic from `nio_tile.py`)
* A tile has 1 pe and a cache (a PE take it's logic from `nio_pe.py`)

```
+---------------+
|  - Memory -   |
+----+ +--+ +---+
     | |  | |
     |R|  |W|
     | |  | |
+----+ +--+ +---+
| ===       === |
||Til| ... |Til||
| ===       === |
.       .       .
.       .       .
.       .       .
| ===       === |
||Til| ... |Til||
| ===       === |
+---------------+


              =========== 
             |           |  
 ===         |  [CACHE]  |   
|Til|  ==    |  [PE]     |
 ===         |           |  
              ===========  

```

## Notes

Please forgive the name here.